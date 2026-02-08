#!/bin/bash
# Reset processed data but KEEP existing plans

echo "🧹 Resetting processed data (keeping plans)..."
echo ""

# Navigate to project root
cd "$(dirname "$0")"

# Remove all processed state data EXCEPT plans
echo "Removing processed state files..."
rm -rf storage/state/manifest.json
rm -rf storage/state/extracted_text/*
rm -rf storage/state/textbook_metadata/*
rm -rf storage/state/coverage/*
rm -rf storage/state/enriched_coverage/*
rm -rf storage/state/chunks/*
rm -rf storage/state/index/*
rm -rf storage/state/embeddings/*

# Keep the directory structure
mkdir -p storage/state/extracted_text
mkdir -p storage/state/textbook_metadata
mkdir -p storage/state/coverage
mkdir -p storage/state/enriched_coverage
mkdir -p storage/state/chunks
mkdir -p storage/state/index
mkdir -p storage/state/embeddings

echo ""
echo "✅ Reset complete!"
echo ""
echo "📁 Kept intact:"
echo "   - storage/uploads/ (your PDFs)"
echo "   - storage/state/plans/ (your study plans)"
echo ""
echo "🗑️  Removed:"
echo "   - All extracted text"
echo "   - All document classifications"
echo "   - All table of contents"
echo "   - All chunks"
echo "   - All embeddings (.npy files)"
echo "   - All FAISS indexes"
echo "   - All coverage files"
echo "   - All enriched coverage"
echo ""
echo "🚀 Ready to reprocess! Your existing plans are preserved."
