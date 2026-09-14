#!/bin/bash

# Demo script for Portsy CLI recordings
cd "/Users/pup/Library/Mobile Documents/com~apple~CloudDocs/Desktop/portsy"

echo "🚀 Portsy Demo - Port Scanner & Route Analyzer"
echo ""
sleep 2

echo "📋 Available scan presets:"
portsy --list-presets
sleep 3
echo ""

echo "🔍 Quick development server scan:"
portsy --preset dev
sleep 5
echo ""

echo "🌐 Comprehensive route discovery:"
portsy --preset dev --comprehensive-routes
sleep 3
echo ""

echo "✅ Demo complete! Try: portsy --preset full"