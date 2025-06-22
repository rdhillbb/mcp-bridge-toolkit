// servermain.go
// Created: 2025-06-22

package main

import (
    "fmt"
    mcp_golang "github.com/metoro-io/mcp-golang"
    "github.com/metoro-io/mcp-golang/transport/stdio"
)

type MyFunctionsArguments struct {
    ZipCode string `json:"zip_code" jsonschema:"required,description=The zip code to be searched"`
}

func main() {
    server := mcp_golang.NewServer(stdio.NewStdioServerTransport())
    
    err := server.RegisterTool("zipcode", "Find an address by his zip code", func(arguments MyFunctionsArguments) (*mcp_golang.ToolResponse, error) {
        // Just return a fake address for any zip code
        fakeAddress := "5954A Bartonsville Road"
        return mcp_golang.NewToolResponse(mcp_golang.NewTextContent(fmt.Sprintf("Your address is %s!", fakeAddress))), nil
    })
    
    if err != nil {
        panic(err)
    }
    
    err = server.Serve()
    if err != nil {
        panic(err)
    }
}
