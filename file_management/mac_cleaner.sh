#!/usr/bin/env bash
set -e  # Exit on error

# Mac Cleanup Tool - Clean up unnecessary files while keeping important data safe
# Version: 1.0.0

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default log file
LOG_FILE="/Users/$(whoami)/Downloads/mac_cleaner_$(date +%Y%m%d_%H%M%S).log"

# Terminal width for progress bars
TERM_WIDTH=$(tput cols 2>/dev/null || echo 80)

# Log levels
LOG_LEVEL_DEBUG=3
LOG_LEVEL_INFO=2
LOG_LEVEL_WARN=1
LOG_LEVEL_ERROR=0

# Default log level
current_log_level=$LOG_LEVEL_INFO

# Progress bar function
show_progress_bar() {
    local percent=$1
    local width=$((TERM_WIDTH - 20))
    local completed=$((width * percent / 100))
    local remaining=$((width - completed))
    
    # Save cursor position
    printf "\033[s"
    
    # Clear current line
    printf "\033[K"
    
    # Print progress bar
    printf "[%s%s] %3d%%" "$(printf "%${completed}s" | tr ' ' '#')" "$(printf "%${remaining}s" | tr ' ' '-')" "$percent"
    
    # Restore cursor position
    printf "\033[u"
}

# Logging functions
log_to_file() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $*" >> "$LOG_FILE"
}

log_debug() {
    log_to_file "[DEBUG] $*"
    if [ $current_log_level -ge $LOG_LEVEL_DEBUG ]; then
        printf "${CYAN}[DEBUG] %s${NC}\n" "$*"
    fi
}

log_info() {
    log_to_file "[INFO] $*"
    if [ $current_log_level -ge $LOG_LEVEL_INFO ]; then
        printf "${GREEN}[INFO] %s${NC}\n" "$*"
    fi
}

log_warn() {
    log_to_file "[WARN] $*"
    if [ $current_log_level -ge $LOG_LEVEL_WARN ]; then
        printf "${YELLOW}[WARN] %s${NC}\n" "$*"
    fi
}

log_error() {
    log_to_file "[ERROR] $*"
    if [ $current_log_level -ge $LOG_LEVEL_ERROR ]; then
        printf "${RED}[ERROR] %s${NC}\n" "$*"
    fi
}

# Format file size for human readable output
format_size() {
    local size=$1
    if [ $size -ge 1048576 ]; then
        printf "${RED}%.2f GB${NC}" $(echo "scale=2; $size/1048576" | bc)
    elif [ $size -ge 1024 ]; then
        printf "${YELLOW}%.2f MB${NC}" $(echo "scale=2; $size/1024" | bc)
    else
        echo "$size KB"
    fi
}

# Show help
show_help() {
    printf "${BLUE}Mac Cleanup Tool v1.0.0${NC}\n"
    echo "Safe cleanup of unnecessary files while preserving important data."
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --help              Show this help message"
    echo "  --dry-run           Simulate cleanup without actually deleting files"
    echo "  --no-confirm        Skip confirmation prompts"
    echo "  --quiet             Quiet mode, only show errors and final results"
    echo "  --verbose           Verbose mode, show more information"
    echo "  --debug             Debug mode, show all information"
    echo "  --exclude-system    Exclude system caches (~/Library/Caches)"
    echo "  --exclude-downloads Exclude ~/Downloads folder"
    echo "  --exclude-documents Exclude ~/Documents folder"
    echo "  --exclude-desktop   Exclude ~/Desktop folder"
    echo "  --custom-path PATH  Add custom path to clean"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run with default settings"
    echo "  $0 --dry-run          # Show what would be cleaned without deleting"
    echo "  $0 --exclude-system   # Exclude system caches from cleanup"
    echo ""
    echo "This script will clean the following by default:"
    echo "  - Xcode derived data and archives"
    echo "  - iOS simulators data"
    echo "  - Docker cache and volumes"
    echo "  - Homebrew cache"
    echo "  - Application caches (~/Library/Caches)"
    echo "  - Trash contents"
    echo "  - Temporary files"
    echo "  - Logs"
    echo ""
    echo "Important: This script uses 'trash' command to move files to the trash"
    echo "instead of permanently deleting them. You can recover items from Trash."
}

# Check for required commands
check_dependencies() {
    log_debug "Checking dependencies..."
    
    if ! command -v trash &> /dev/null; then
        log_error "Missing 'trash' command. Install with: brew install trash"
        exit 1
    fi
    
    if ! command -v du &> /dev/null; then
        log_error "Missing 'du' command. This is required for calculating sizes."
        exit 1
    fi
    
    if ! command -v find &> /dev/null; then
        log_error "Missing 'find' command. This is required for finding files."
        exit 1
    fi
    
    log_info "All dependencies found."
}

# Initialize variables
dry_run=false
no_confirm=false
exclude_system=false
exclude_downloads=false
exclude_documents=false
exclude_desktop=false
custom_paths=()
skip_confirmation=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --help)
            show_help
            exit 0
            ;;
        --dry-run)
            dry_run=true
            shift
            ;;
        --no-confirm)
            no_confirm=true
            shift
            ;;
        --quiet)
            current_log_level=$LOG_LEVEL_ERROR
            shift
            ;;
        --verbose)
            current_log_level=$LOG_LEVEL_INFO
            shift
            ;;
        --debug)
            current_log_level=$LOG_LEVEL_DEBUG
            shift
            ;;
        --exclude-system)
            exclude_system=true
            shift
            ;;
        --exclude-downloads)
            exclude_downloads=true
            shift
            ;;
        --exclude-documents)
            exclude_documents=true
            shift
            ;;
        --exclude-desktop)
            exclude_desktop=true
            shift
            ;;
        --custom-path)
            custom_paths+=("$2")
            shift 2
            ;;
        -*)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
        *)
            log_error "Unexpected argument: $1"
            show_help
            exit 1
            ;;
    esac
done

# Define cleanup paths and patterns
declare -A cleanup_paths

# Xcode derived data and archives
cleanup_paths["~/Library/Developer/Xcode/DerivedData"]="*.xcactivitylog *.xcuserstate"
cleanup_paths["~/Library/Developer/Xcode/Archives"]="*.xcarchive"

# iOS Simulator data
cleanup_paths["~/Library/Developer/CoreSimulator"]="*"

# Docker cache
if command -v docker &> /dev/null; then
    cleanup_paths["docker_system"]="docker system prune -af"
    cleanup_paths["docker_builder"]="docker builder prune -af"
fi

# Homebrew cache
if command -v brew &> /dev/null; then
    cleanup_paths["homebrew_cache"]="brew cleanup"
fi

# Application caches (unless excluded)
if [ "$exclude_system" = false ]; then
    cleanup_paths["~/Library/Caches"]="*"
fi

# Downloads folder (unless excluded)
if [ "$exclude_downloads" = false ]; then
    cleanup_paths["~/Downloads"]="*.tmp *.temp *.log *.dmg *.pkg *.zip *.tar.gz *.app"
fi

# Documents folder (unless excluded)
if [ "$exclude_documents" = false ]; then
    cleanup_paths["~/Documents"]="*.tmp *.temp *.log *.dmg"
fi

# Desktop folder (unless excluded)
if [ "$exclude_desktop" = false ]; then
    cleanup_paths["~/Desktop"]="*.tmp *.temp *.log *.dmg *.pkg"
fi

# Temporary files
cleanup_paths["/tmp"]="*"

# Add custom paths if provided
for custom_path in "${custom_paths[@]}"; do
    cleanup_paths["$custom_path"]="*"
done

# Trash cleanup (always included)
cleanup_paths["~/.Trash"]="*"

# Find and calculate size of files to clean
calculate_files_size() {
    local total_size=0
    
    for path in "${!cleanup_paths[@]}"; do
        if [[ "$path" == "docker_"* ]] || [[ "$path" == "homebrew_cache" ]]; then
            # These are commands, not file paths
            continue
        fi
        
        local full_path="${path/#\~/$HOME}"
        if [ -d "$full_path" ]; then
            local pattern="${cleanup_paths[$path]}"
            local size=$(find "$full_path" -name "$pattern" -type f -exec du -sk {} + 2>/dev/null | awk '{sum += $1} END {print sum}' || echo 0)
            total_size=$((total_size + size))
        fi
    done
    
    echo $total_size
}

# Main cleanup function
perform_cleanup() {
    local items_processed=0
    local items_total=0
    local success_count=0
    local failed_count=0
    local skipped_count=0
    local total_size=0
    
    # Calculate total items to process
    for path in "${!cleanup_paths[@]}"; do
        if [[ "$path" == "docker_"* ]] || [[ "$path" == "homebrew_cache" ]]; then
            items_total=$((items_total + 1))
        else
            local full_path="${path/#\~/$HOME}"
            if [ -d "$full_path" ]; then
                local pattern="${cleanup_paths[$path]}"
                local count=$(find "$full_path" -name "$pattern" -type f 2>/dev/null | wc -l | tr -d ' ')
                items_total=$((items_total + count))
            fi
        fi
    done
    
    # Add one more for trash
    items_total=$((items_total + 1))
    
    log_info "Starting cleanup process..."
    log_info "Total items to process: $items_total"
    
    # Print progress bar line
    printf "\n"
    show_progress_bar 0
    
    # Process each cleanup path
    for path in "${!cleanup_paths[@]}"; do
        if [[ "$path" == "docker_"* ]]; then
            # Special handling for Docker commands
            if [ "$dry_run" = false ]; then
                log_info "Running: ${cleanup_paths[$path]}"
                if eval "${cleanup_paths[$path]}" >> "$LOG_FILE" 2>&1; then
                    success_count=$((success_count + 1))
                    log_info "Docker cleanup completed"
                else
                    failed_count=$((failed_count + 1))
                    log_error "Docker cleanup failed"
                fi
            else
                log_info "[DRY RUN] Would run: ${cleanup_paths[$path]}"
            fi
            items_processed=$((items_processed + 1))
            local percent=$((items_processed * 100 / items_total))
            show_progress_bar $percent
            continue
        elif [[ "$path" == "homebrew_cache" ]]; then
            # Special handling for Homebrew cache
            if [ "$dry_run" = false ]; then
                log_info "Running: ${cleanup_paths[$path]}"
                if eval "${cleanup_paths[$path]}" >> "$LOG_FILE" 2>&1; then
                    success_count=$((success_count + 1))
                    log_info "Homebrew cache cleanup completed"
                else
                    failed_count=$((failed_count + 1))
                    log_error "Homebrew cache cleanup failed"
                fi
            else
                log_info "[DRY RUN] Would run: ${cleanup_paths[$path]}"
            fi
            items_processed=$((items_processed + 1))
            local percent=$((items_processed * 100 / items_total))
            show_progress_bar $percent
            continue
        fi
        
        # Regular file paths
        local full_path="${path/#\~/$HOME}"
        if [ ! -d "$full_path" ]; then
            log_debug "Skipping non-existent path: $full_path"
            skipped_count=$((skipped_count + 1))
            items_processed=$((items_processed + 1))
            local percent=$((items_processed * 100 / items_total))
            show_progress_bar $percent
            continue
        fi
        
        local pattern="${cleanup_paths[$path]}"
        log_debug "Processing path: $full_path with pattern: $pattern"
        
        # Find files to process
        local files=()
        while IFS= read -r -d '' file; do
            files+=("$file")
        done < <(find "$full_path" -name "$pattern" -type f -print0 2>/dev/null)
        
        # Process each file
        for file in "${files[@]}"; do
            if [ ! -f "$file" ]; then
                skipped_count=$((skipped_count + 1))
                items_processed=$((items_processed + 1))
                continue
            fi
            
            local size=$(du -sk "$file" 2>/dev/null | cut -f1 || echo 0)
            total_size=$((total_size + size))
            
            if [ "$dry_run" = false ]; then
                log_debug "Moving to trash: $file"
                if trash "$file" 2>>"$LOG_FILE"; then
                    success_count=$((success_count + 1))
                    log_to_file "Successfully moved to trash: $file"
                else
                    failed_count=$((failed_count + 1))
                    log_error "Failed to move to trash: $file"
                fi
            else
                log_info "[DRY RUN] Would move to trash: $file ($(format_size $size))"
            fi
            
            items_processed=$((items_processed + 1))
            local percent=$((items_processed * 100 / items_total))
            show_progress_bar $percent
        done
    done
    
    # Empty trash if not in dry run mode
    if [ "$dry_run" = false ]; then
        log_info "Emptying trash..."
        if osascript -e 'tell application "Finder" to empty trash' >> "$LOG_FILE" 2>&1; then
            success_count=$((success_count + 1))
            log_info "Trash emptied successfully"
        else
            failed_count=$((failed_count + 1))
            log_error "Failed to empty trash"
        fi
    else
        log_info "[DRY RUN] Would empty trash"
    fi
    
    items_processed=$((items_processed + 1))
    show_progress_bar 100
    printf "\n\n"
    
    # Final summary
    log_info "Cleanup completed!"
    log_info "Successfully processed: $success_count items"
    log_info "Skipped: $skipped_count items"
    if [ $failed_count -gt 0 ]; then
        log_error "Failed: $failed_count items"
    fi
    log_info "Total space that would be freed: $(format_size $total_size)"
    log_info "Log file saved to: $LOG_FILE"
}

# Main execution
main() {
    # Show banner
    log_info "========================================"
    log_info "Mac Cleanup Tool v1.0.0"
    log_info "========================================"
    
    # Check dependencies
    check_dependencies
    
    # Show configuration
    log_info "Configuration:"
    log_info "  Dry run mode: $dry_run"
    log_info "  No confirm mode: $no_confirm"
    log_info "  Exclude system caches: $exclude_system"
    log_info "  Exclude downloads: $exclude_downloads"
    log_info "  Exclude documents: $exclude_documents"
    log_info "  Exclude desktop: $exclude_desktop"
    if [ ${#custom_paths[@]} -gt 0 ]; then
        log_info "  Custom paths: ${custom_paths[*]}"
    fi
    
    # Show what will be cleaned
    log_info "Paths to be cleaned:"
    for path in "${!cleanup_paths[@]}"; do
        if [[ "$path" == "docker_"* ]] || [[ "$path" == "homebrew_cache" ]]; then
            log_info "  - $path: ${cleanup_paths[$path]}"
        else
            log_info "  - $path (pattern: ${cleanup_paths[$path]})"
        fi
    done
    
    # Calculate and show size
    if [ "$dry_run" = false ]; then
        log_info "Calculating size of files to clean..."
        total_size=$(calculate_files_size)
        log_info "Estimated space to free: $(format_size $total_size)"
    fi
    
    # Confirmation prompt
    if [ "$no_confirm" = false ] && [ "$dry_run" = false ]; then
        printf "${YELLOW}Do you want to proceed with the cleanup? Type 'yes' to confirm: ${NC}"
        read -r confirm
        if [ "$confirm" != "yes" ]; then
            log_warn "Operation cancelled by user."
            exit 0
        fi
    fi
    
    # Perform cleanup
    perform_cleanup
}

# Run main function
main "$@"