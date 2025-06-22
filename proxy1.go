// proxy1.go
// Created: 2025-06-22

package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
)

type ProxyServer struct {
	targetURL string
	client    *http.Client
}

func NewProxyServer(targetURL string) *ProxyServer {
	return &ProxyServer{
		targetURL: targetURL,
		client:    &http.Client{},
	}
}

func (p *ProxyServer) handleStdio() {
	scanner := bufio.NewScanner(os.Stdin)
	
	for scanner.Scan() {
		line := scanner.Text()
		if line == "" {
			continue
		}
		
		// Parse JSON-RPC message from stdin
		var request map[string]interface{}
		if err := json.Unmarshal([]byte(line), &request); err != nil {
			log.Printf("Error parsing JSON: %v", err)
			continue
		}
		
		// Forward to target MCP server
		response, err := p.forwardRequest(request)
		if err != nil {
			log.Printf("Error forwarding request: %v", err)
			// Send error response back to stdout
			errorResponse := map[string]interface{}{
				"jsonrpc": "2.0",
				"error": map[string]interface{}{
					"code":    -32603,
					"message": "Internal error",
				},
			}
			if id, exists := request["id"]; exists {
				errorResponse["id"] = id
			}
			p.sendResponse(errorResponse)
			continue
		}
		
		// Send response back to stdout
		p.sendResponse(response)
	}
	
	if err := scanner.Err(); err != nil {
		log.Printf("Error reading from stdin: %v", err)
	}
}

func (p *ProxyServer) forwardRequest(request map[string]interface{}) (map[string]interface{}, error) {
	// Convert request to JSON
	requestBody, err := json.Marshal(request)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %v", err)
	}
	
	// Create HTTP request
	httpReq, err := http.NewRequest("POST", p.targetURL, bytes.NewBuffer(requestBody))
	if err != nil {
		return nil, fmt.Errorf("failed to create HTTP request: %v", err)
	}
	
	httpReq.Header.Set("Content-Type", "application/json")
	
	// Send request
	resp, err := p.client.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %v", err)
	}
	defer resp.Body.Close()
	
	// Read response
	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %v", err)
	}
	
	// Parse response
	var response map[string]interface{}
	if err := json.Unmarshal(responseBody, &response); err != nil {
		return nil, fmt.Errorf("failed to parse response: %v", err)
	}
	
	return response, nil
}

func (p *ProxyServer) sendResponse(response map[string]interface{}) {
	responseJSON, err := json.Marshal(response)
	if err != nil {
		log.Printf("Error marshaling response: %v", err)
		return
	}
	
	fmt.Println(string(responseJSON))
}

func main() {
	if len(os.Args) < 2 {
		log.Fatal("Usage: go run proxy.go <target-url>")
	}
	
	targetURL := os.Args[1]
	log.Printf("Starting MCP proxy, forwarding to: %s", targetURL)
	
	proxy := NewProxyServer(targetURL)
	proxy.handleStdio()
}
