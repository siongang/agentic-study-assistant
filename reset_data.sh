#!/bin/bash
# Reset all processed data while keeping uploaded files

echo "🧹 Resetting all processed data..."
echo ""

# Navigate to project root
cd "$(dirname "$0")"

# Remove all processed state data
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

# Remove generated plans
echo "Removing generated plans..."
rm -rf storage/state/plans/*.json
rm -rf storage/state/plans/*.md
rm -rf storage/state/plans/*.csv
rm -rf storage/plans/*.json 2>/dev/null
rm -rf storage/plans/*.md 2>/dev/null
rm -rf storage/plans/*.csv 2>/dev/null

# Keep uploads directory intact
echo ""
echo "✅ Reset complete!"
echo ""
echo "📁 Kept intact:"
echo "   - storage/uploads/ (your PDFs are safe)"
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
echo "   - All generated plans"
echo ""
echo "🚀 Ready for a fresh start! Run your agent to reprocess files."
