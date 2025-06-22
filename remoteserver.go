// remoteserver.go
// Created: 2025-06-22

package main

import (
	"fmt"
	"log"
	"time"

	mcp_golang "github.com/metoro-io/mcp-golang"
	"github.com/metoro-io/mcp-golang/transport/http"
)

// Struct for remote_address_lookup
type MyFunctionsArguments struct {
	ZipCode string `json:"zip_code" jsonschema:"required,description=The zip code to be searched"`
}

// Struct for time tool
type TimeArgs struct {
	Format string `json:"format" jsonschema:"description=The time format to use"`
}

func main() {
	// Use HTTP transport to match client expectation
	transport := http.NewHTTPTransport("/mcp").WithAddr(":8080")

	// Create the MCP server
	server := mcp_golang.NewServer(
		transport,
		mcp_golang.WithName("remote-address-lookup-server"),
		mcp_golang.WithInstructions("A remote address lookup server that returns fake addresses for zip codes"),
		mcp_golang.WithVersion("0.0.1"),
	)

	// Register remote_address_lookup tool
	err := server.RegisterTool(
		"remote_address_lookup",
		"Find an address by his zip code",
		func(arguments MyFunctionsArguments) (*mcp_golang.ToolResponse, error) {
			if arguments.ZipCode == "" {
				return nil, fmt.Errorf("zip_code is required")
			}

			responseText := fmt.Sprintf(
				"Address found for zip code %s: 5954A Bartonsville Road, Fakeville, NY %s, USA",
				arguments.ZipCode,
				arguments.ZipCode,
			)

			return mcp_golang.NewToolResponse(mcp_golang.NewTextContent(responseText)), nil
		},
	)
	if err != nil {
		log.Fatalf("Failed to register remote_address_lookup tool: %v", err)
	}

	// Register time tool (copied from hellotest.go)
	err = server.RegisterTool(
		"time",
		"Returns the current time in the specified format",
		func(args TimeArgs) (*mcp_golang.ToolResponse, error) {
			format := args.Format
			return mcp_golang.NewToolResponse(mcp_golang.NewTextContent(time.Now().Format(format))), nil
		},
	)
	if err != nil {
		log.Fatalf("Failed to register time tool: %v", err)
	}

	// Start the server
	log.Println("Starting remote address lookup server with HTTP transport...")
	if err := server.Serve(); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}

