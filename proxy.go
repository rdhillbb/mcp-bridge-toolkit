// proxy.go
// Created: 2025-06-22

package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
	"os"
	"os/signal"
	"path/filepath"
	"runtime"
	"sync"
	"syscall"
	"time"
)

type ProxyServer struct {
	targetURL   string
	client      *http.Client
	logger      *log.Logger
	logFile     *os.File
	logWriter   *bufio.Writer
	mu          sync.Mutex
	ctx         context.Context
	cancel      context.CancelFunc
}

func NewProxyServer(targetURL string, logger *log.Logger, logFile *os.File, logWriter *bufio.Writer) *ProxyServer {
	ctx, cancel := context.WithCancel(context.Background())
	return &ProxyServer{
		targetURL: targetURL,
		client: &http.Client{
			Timeout: 30 * time.Second,
		},
		logger:    logger,
		logFile:   logFile,
		logWriter: logWriter,
		ctx:       ctx,
		cancel:    cancel,
	}
}

// logAndFlush logs a message and immediately flushes to disk
func (p *ProxyServer) logAndFlush(format string, v ...interface{}) {
	p.mu.Lock()
	defer p.mu.Unlock()
	
	p.logger.Printf(format, v...)
	// Flush the buffered writer
	if err := p.logWriter.Flush(); err != nil {
		log.Printf("Failed to flush log buffer: %v", err)
	}
	// Sync to disk
	if err := p.logFile.Sync(); err != nil {
		log.Printf("Failed to sync log file: %v", err)
	}
}

func (p *ProxyServer) handleStdio() {
	p.logAndFlush("Starting MCP proxy with streaming HTTP transport")
	
	// Start HTTP streaming connection
	errChan := make(chan error, 2)
	
	// Start goroutine to handle stdin -> HTTP
	go p.handleStdinToHTTP(errChan)
	
	// Start goroutine to handle HTTP -> stdout  
	go p.handleHTTPToStdout(errChan)
	
	// Wait for either goroutine to fail or context cancellation
	select {
	case err := <-errChan:
		p.logAndFlush("Error in proxy goroutine: %v", err)
	case <-p.ctx.Done():
		p.logAndFlush("Context cancelled, shutting down proxy")
	}
	
	p.cancel()
	p.logAndFlush("Proxy shutdown complete")
}

func (p *ProxyServer) handleStdinToHTTP(errChan chan<- error) {
	p.logAndFlush("Starting stdin->HTTP message relay")
	
	scanner := bufio.NewScanner(os.Stdin)
	messageCount := 0
	
	for scanner.Scan() {
		select {
		case <-p.ctx.Done():
			return
		default:
		}
		
		line := scanner.Text()
		if line == "" {
			continue
		}
		
		messageCount++
		p.logAndFlush("=== Message #%d from stdin ===", messageCount)
		p.logAndFlush("Raw input: %s", line)
		
		// Parse and validate JSON-RPC message
		var request map[string]interface{}
		if err := json.Unmarshal([]byte(line), &request); err != nil {
			p.logAndFlush("ERROR: Invalid JSON from stdin: %v", err)
			p.sendErrorResponse(request, -32700, "Parse error", err)
			continue
		}
		
		// Forward to HTTP server and get response
		response, err := p.forwardJSONRPCRequest(request)
		if err != nil {
			p.logAndFlush("ERROR: Failed to forward request: %v", err)
			p.sendErrorResponse(request, -32603, "Internal error", err)
			continue
		}
		
		// Send response to stdout
		p.sendJSONResponse(response)
		p.logAndFlush("=== Message #%d completed ===\n", messageCount)
	}
	
	if err := scanner.Err(); err != nil {
		errChan <- fmt.Errorf("error reading stdin: %v", err)
		return
	}
	
	p.logAndFlush("Stdin handler completed")
}

func (p *ProxyServer) handleHTTPToStdout(errChan chan<- error) {
	// For MCP, the server typically only responds to requests
	// Notifications from server to client are rare
	// This could be extended later if needed
	<-p.ctx.Done()
}

func (p *ProxyServer) forwardJSONRPCRequest(request map[string]interface{}) (map[string]interface{}, error) {
	// Convert request to JSON
	requestBody, err := json.Marshal(request)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %v", err)
	}
	
	p.logAndFlush("HTTP request body: %s", string(requestBody))
	
	// Create HTTP request with JSON body
	req, err := http.NewRequestWithContext(p.ctx, "POST", p.targetURL, 
		bytes.NewBuffer(requestBody))
	if err != nil {
		return nil, fmt.Errorf("failed to create HTTP request: %v", err)
	}
	
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")
	
	// Send request
	startTime := time.Now()
	resp, err := p.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("HTTP request failed: %v", err)
	}
	defer resp.Body.Close()
	
	elapsed := time.Since(startTime)
	p.logAndFlush("HTTP response received in %v - Status: %s", elapsed, resp.Status)
	
	// Read response body
	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %v", err)
	}
	
	p.logAndFlush("HTTP response body: %s", string(responseBody))
	
	// Parse JSON response
	var response map[string]interface{}
	if err := json.Unmarshal(responseBody, &response); err != nil {
		return nil, fmt.Errorf("failed to parse response JSON: %v", err)
	}
	
	return response, nil
}

func (p *ProxyServer) sendErrorResponse(request map[string]interface{}, code int, message string, err error) {
	errorResponse := map[string]interface{}{
		"jsonrpc": "2.0",
		"error": map[string]interface{}{
			"code":    code,
			"message": fmt.Sprintf("%s: %v", message, err),
		},
	}
	
	if id, exists := request["id"]; exists {
		errorResponse["id"] = id
	}
	
	p.sendJSONResponse(errorResponse)
}

func (p *ProxyServer) sendJSONResponse(response map[string]interface{}) {
	responseJSON, err := json.Marshal(response)
	if err != nil {
		p.logAndFlush("ERROR: Failed to marshal response: %v", err)
		return
	}
	
	p.logAndFlush("Sending to stdout: %s", string(responseJSON))
	fmt.Println(string(responseJSON))
	os.Stdout.Sync()
}

func createLogger(targetURL string) (*log.Logger, *os.File, *bufio.Writer, string, error) {
	// Extract port number from URL
	portNumber := "unknown"
	if u, err := url.Parse(targetURL); err == nil {
		if u.Port() != "" {
			portNumber = u.Port()
		} else {
			// Default ports for common schemes
			switch u.Scheme {
			case "http":
				portNumber = "80"
			case "https":
				portNumber = "443"
			default:
				portNumber = "noport"
			}
		}
	}
	
	// Try multiple locations in order of preference
	logDirs := []string{
		"/Users/randolphhill/.mcpproxy/logs", // Your preferred location
		filepath.Join(os.Getenv("HOME"), ".mcpproxy", "logs"), // Fallback to home
		"./logs",                 // Current directory
		os.TempDir(),            // Temp directory (fallback)
	}
	
	now := time.Now()
	filename := fmt.Sprintf("%s_%02d%02d%02d%02d%02d%02d.log",
		portNumber,
		now.Month(), now.Day(), now.Year()%100,
		now.Hour(), now.Minute(), now.Second())
	
	var file *os.File
	var logPath string
	var err error
	
	for _, dir := range logDirs {
		// Create directory if it doesn't exist
		if err := os.MkdirAll(dir, 0755); err != nil {
			log.Printf("Cannot create directory %s: %v", dir, err)
			continue
		}
		
		logPath = filepath.Join(dir, filename)
		file, err = os.OpenFile(logPath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
		if err == nil {
			log.Printf("Successfully created log file: %s", logPath)
			break
		}
		log.Printf("Cannot create log file at %s: %v", logPath, err)
	}
	
	if file == nil {
		return nil, nil, nil, "", fmt.Errorf("failed to create log file in any location")
	}
	
	// Create a buffered writer for better performance
	bufWriter := bufio.NewWriter(file)
	
	// Create logger that writes to the buffered writer
	logger := log.New(bufWriter, "", log.Ldate|log.Ltime|log.Lmicroseconds|log.Lshortfile)
	
	// Log startup information
	logger.Printf("=== MCP Proxy Log Started ===")
	logger.Printf("Target URL: %s", targetURL)
	logger.Printf("Port Number: %s", portNumber)
	logger.Printf("Log file: %s", logPath)
	logger.Printf("Process ID: %d", os.Getpid())
	
	// Handle os.Executable() properly
	if execPath, execErr := os.Executable(); execErr != nil {
		logger.Printf("Executable: error getting path: %v", execErr)
	} else {
		logger.Printf("Executable: %s", execPath)
	}
	
	logger.Printf("Go version: %s", runtime.Version())
	logger.Printf("GOOS: %s, GOARCH: %s", runtime.GOOS, runtime.GOARCH)
	
	// Flush startup info
	bufWriter.Flush()
	file.Sync()
	
	// Also print to stderr so user knows where log is
	log.Printf("Logging to: %s", logPath)
	
	return logger, file, bufWriter, logPath, nil
}

func main() {
	if len(os.Args) < 2 {
		log.Fatal("Usage: go run proxy.go <target-url>")
	}
	
	targetURL := os.Args[1]
	
	// Create logger
	logger, logFile, bufWriter, logPath, err := createLogger(targetURL)
	if err != nil {
		log.Fatalf("Failed to create logger: %v", err)
	}
	
	// Create cleanup function
	cleanup := func() {
		logger.Printf("=== Cleanup started ===")
		logger.Printf("Flushing log buffer...")
		
		// Flush the buffered writer
		if err := bufWriter.Flush(); err != nil {
			log.Printf("Error flushing buffer: %v", err)
		}
		
		// Sync the file to disk
		if err := logFile.Sync(); err != nil {
			log.Printf("Error syncing file: %v", err)
		}
		
		logger.Printf("=== MCP Proxy Log Ended ===")
		
		// Final flush and sync
		bufWriter.Flush()
		logFile.Sync()
		
		// Close the file
		if err := logFile.Close(); err != nil {
			log.Printf("Error closing log file: %v", err)
		}
		
		log.Printf("Log file closed: %s", logPath)
	}
	
	// Ensure cleanup runs on normal exit
	defer cleanup()
	
	// Set up signal handling for graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM, syscall.SIGQUIT, syscall.SIGHUP)
	
	proxy := NewProxyServer(targetURL, logger, logFile, bufWriter)
	
	// Handle signals in a goroutine
	go func() {
		sig := <-sigChan
		logger.Printf("Received signal: %v", sig)
		proxy.cancel() // Cancel the context
		bufWriter.Flush()
		logFile.Sync()
		cleanup()
		os.Exit(0)
	}()
	
	// Create a helper function for logging with flush
	logAndFlush := func(format string, v ...interface{}) {
		logger.Printf(format, v...)
		bufWriter.Flush()
		logFile.Sync()
	}
	
	// Log startup info
	logAndFlush("Starting MCP proxy")
	logAndFlush("Target URL: %s", targetURL)
	logAndFlush("Arguments: %v", os.Args)
	logAndFlush("Current directory: %s", mustGetwd())
	logAndFlush("Environment PATH: %s", os.Getenv("PATH"))
	
	// Also log to stderr for immediate feedback
	log.Printf("Starting MCP proxy, forwarding to: %s", targetURL)
	
	// Handle panic recovery
	defer func() {
		if r := recover(); r != nil {
			logAndFlush("PANIC: %v", r)
			logAndFlush("Stack trace:")
			
			// Get stack trace
			buf := make([]byte, 4096)
			n := runtime.Stack(buf, false)
			logAndFlush("%s", string(buf[:n]))
			
			// Ensure everything is written
			cleanup()
			
			// Re-panic to get default behavior
			panic(r)
		}
	}()
	
	proxy.handleStdio()
	
	logAndFlush("Proxy main function ending normally")
}

func mustGetwd() string {
	wd, err := os.Getwd()
	if err != nil {
		return fmt.Sprintf("error: %v", err)
	}
	return wd
}
