#!/bin/bash
# Restore from backup script

BACKUP_DIR="backend_backup_working_20251226_103605"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Backup directory $BACKUP_DIR not found!"
    exit 1
fi

echo "🔄 Restoring backend from backup: $BACKUP_DIR"
echo "⚠️  This will overwrite the current backend directory!"
read -p "Are you sure? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Create a backup of current state before restoring
    CURRENT_BACKUP="backend_before_restore_$(date +%Y%m%d_%H%M%S)"
    echo "📦 Creating backup of current state: $CURRENT_BACKUP"
    cp -r backend "$CURRENT_BACKUP"
    
    # Remove current backend and restore from backup
    echo "🗑️  Removing current backend..."
    rm -rf backend
    
    echo "📁 Restoring from backup..."
    cp -r "$BACKUP_DIR" backend
    
    echo "✅ Backup restored successfully!"
    echo "📦 Previous state saved as: $CURRENT_BACKUP"
else
    echo "❌ Restore cancelled"
fi