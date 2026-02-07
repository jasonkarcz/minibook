#!/usr/bin/env python
#
# minibook_pypdf.py
#
# A fully Pythonic version using the 'pypdf' library for cross-platform PDF manipulation.
# This removes all reliance on external executables (pstops, ps2pdf, etc.).
#
# Required external Python dependency: pypdf (install via `pip install pypdf`)
#

import argparse
import sys
import os
from math import ceil
from pypdf import PdfReader, PdfWriter, Transformation, PaperSize, PageObject

# --- Constants ---

# Standard US Letter dimensions in points (fallback, though dimensions are dynamic)
DEFAULT_LETTER_WIDTH = 612 # 8.5 * 72
DEFAULT_LETTER_HEIGHT = 792 # 11 * 72

# --- Logging Functions ---

def status(args, message):
    """Prints a status message to stderr if verbose mode is enabled."""
    if args.v or args.vv:
        sys.stderr.write(f"# {message}\n\n")

def debug(args, message):
    """Prints a debug message to stderr if debug mode is enabled."""
    if args.vv:
        sys.stderr.write(f"# {message}\n\n")

# --- Core Imposition Logic ---

def create_blank_page(width, height):
    """Creates a new, simple blank PageObject with the specified dimensions."""
    blank = PageObject.create_blank_page(width=width, height=height)
    return blank

def pad_pages(reader, final_width, final_height, args):
    """
    Pads the PDF with blank pages so the total count is a multiple of 8.
    Returns a new list of all pages (original + blank padding).
    """
    
    original_pages = list(reader.pages)
    nump = len(original_pages)
    
    if nump % 8 == 0:
        debug(args, f"Page count ({nump}) is already a multiple of 8.")
        return original_pages

    # Calculate padding needed to reach the next multiple of 8
    target_nump = 8 * ceil(nump / 8)
    padding_needed = target_nump - nump
    
    status(args, f"Original pages: {nump}. Padding with {padding_needed} blank pages to reach {target_nump}.")
    
    blank_pages = []
    for _ in range(padding_needed):
        # Create blank pages matching the final sheet size
        blank_pages.append(create_blank_page(final_width, final_height))
        
    return original_pages + blank_pages

def run_minibook(args):
    """
    Main logic to process files and generate the minibook using pypdf.
    """
    
    # --- 1. I/O Setup and Reading ---
    
    if args.infile is None or args.infile == '-':
        sys.stderr.write("Error: This Pythonic version requires a named PDF input file (not STDIN).\n")
        sys.exit(1)
        
    if not os.path.exists(args.infile):
        sys.stderr.write(f"Error: Input file not found: {args.infile}\n")
        sys.exit(1)

    status(args, f"Reading input PDF: {args.infile}")
    
    try:
        reader = PdfReader(args.infile)
    except Exception as e:
        sys.stderr.write(f"Error reading PDF file: {e}\n")
        sys.exit(1)
        
    nump_original = len(reader.pages)
    if nump_original == 0:
        sys.stderr.write("Error: Input PDF contains no pages.\n")
        sys.exit(1)
        
    # --- 2. Determine Dynamic Page Sizes ---
    
    # Get the size of the first page to use as the template for all operations.
    first_page_box = reader.pages[0].cropbox
    FINAL_WIDTH = float(first_page_box.width)
    FINAL_HEIGHT = float(first_page_box.height)
    
    # Calculate dimensions for the intermediate spread page
    SPREAD_WIDTH = FINAL_WIDTH
    SPREAD_HEIGHT = FINAL_HEIGHT / 2
    
    debug(args, f"Detected Input Page Size: {FINAL_WIDTH} x {FINAL_HEIGHT} points")
    debug(args, f"Spread Page Size: {SPREAD_WIDTH} x {SPREAD_HEIGHT} points")
    
    # --- 3. Padding ---
    
    # Padded pages list (length is a multiple of 8)
    pages = pad_pages(reader, FINAL_WIDTH, FINAL_HEIGHT, args)
    nump = len(pages)
    num_spreads = nump // 2
    num_final_sheets = nump // 4
    
    # --- 4. Phase 1: Horizontal Stitching (N/2 Spreads) ---
    
    status(args, "Phase 1: Creating N/2 horizontal spreads.")
    spread_pages = [] # List to hold the intermediate SPREAD_HEIGHT spreads
    
    # Transformation to scale pages down by 50%
    scale_transform = Transformation().scale(0.5, 0.5)
    
    for i in range(1, num_spreads + 1):
        front_page_idx = i - 1
        back_page_idx = nump - i
        
        # Get pages. pypdf uses 0-based indexing.
        P_Front = pages[front_page_idx]
        P_Back = pages[back_page_idx]
        
        # Create the new canvas page for the spread (SPREAD_WIDTH x SPREAD_HEIGHT)
        spread_canvas = create_blank_page(SPREAD_WIDTH, SPREAD_HEIGHT)

        # Define translation for the right page: half the width
        # Note: Left page tx=0, ty=0
        right_page_tx = SPREAD_WIDTH / 2
        
        # Conditional layout rule
        if i % 2 != 0:
            # Odd iteration: Back page on Left (0, 0), Front page on Right
            P_L, P_R = P_Back, P_Front
            debug(args, f"Spread {i} (Odd): Back({back_page_idx+1}) on Left, Front({front_page_idx+1}) on Right.")
        else:
            # Even iteration: Front page on Left (0, 0), Back page on Right
            P_L, P_R = P_Front, P_Back
            debug(args, f"Spread {i} (Even): Front({front_page_idx+1}) on Left, Back({back_page_idx+1}) on Right.")

        # Place the pages onto the spread canvas, applying the scaling transformation directly.
        # This is non-destructive to the original page objects.
        
        # Left Page: scaled and translated to (0, 0)
        transform_L = scale_transform.translate(tx=0, ty=0)
        spread_canvas.merge_transformed_page(P_L, transform_L)
        
        # Right Page: scaled and translated to (SPREAD_WIDTH / 2, 0)
        transform_R = scale_transform.translate(tx=right_page_tx, ty=0)
        spread_canvas.merge_transformed_page(P_R, transform_R)
        
        # Add the resulting spread to the list
        spread_pages.append(spread_canvas)

    # --- 5. Phase 2: Vertical Stitching and Rotation (N/4 Final Sheets) ---
    
    status(args, "Phase 2: Stitching spreads vertically with rotation (Final Sheet Size).")
    final_writer = PdfWriter()
    
    for j in range(num_final_sheets):
        # Spreads from Phase 1 are indexed 0 to num_spreads - 1
        top_spread_idx = j
        bottom_spread_idx = num_spreads - j - 1
        
        # Get spreads (no need to copy them)
        S_Top = spread_pages[top_spread_idx]
        S_Bottom = spread_pages[bottom_spread_idx]
        
        # Create the final-sized canvas
        final_canvas = create_blank_page(FINAL_WIDTH, FINAL_HEIGHT)

        # Top Spread (j): Unrotated, placed on the top half (ty=SPREAD_HEIGHT).
        translate_top = Transformation().translate(tx=0, ty=SPREAD_HEIGHT)
        final_canvas.merge_transformed_page(S_Top, translate_top)
        
        # Bottom Spread: Rotated 180 degrees, placed on the bottom half (ty=0).
        # FIX: Apply transformations directly to the PageObject to avoid
        # unsupported composition operators.
        
        # 1. Rotate the page 180 degrees around its origin (0,0)
        # S_Bottom.rotate(180) <-- This was not working as expected.
        # FIX: Use .add_transformation() for rotation as requested.
        rotate_transform = Transformation().rotate(180)
        S_Bottom.add_transformation(rotate_transform)
        
        # 2. Translate the *already rotated* page to its final position.
        # The correct position for the rotated page's origin is (WIDTH, HEIGHT).
        translate_transform = Transformation().translate(tx=SPREAD_WIDTH, ty=SPREAD_HEIGHT)
        S_Bottom.add_transformation(translate_transform)
        
        # 3. Merge the fully transformed page onto the canvas.
        final_canvas.merge_page(S_Bottom)

        debug(args, f"Final Sheet {j+1}: Top Spread ({top_spread_idx+1}) unrotated, Bottom Spread ({bottom_spread_idx+1}) rotated 180°.")
        final_writer.add_page(final_canvas)

    # --- 6. Output ---
    
    outfile_path = args.outfile or '-'
    if outfile_path == '-':
        status(args, "Output set to: - (STDOUT). Note: Writing PDF binary to STDOUT.")
        # Writing PDF binary data to stdout buffer
        final_writer.write(sys.stdout.buffer)
    else:
        basename = os.path.splitext(args.infile)[0]
        if args.outfile is None:
            outfile_path = f"{basename}.minibook.pdf"
        
        status(args, f"Writing final PDF to: {outfile_path}")
        try:
            with open(outfile_path, "wb") as f:
                final_writer.write(f)
        except Exception as e:
            sys.stderr.write(f"Error writing output file: {e}\n")
            raise

    status(args, "Process complete.")
                
def main():
    """Parses arguments and initiates the script."""
    
    parser = argparse.ArgumentParser(
        description="Create a- miniature booklet from any PDF file using pypdf.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "This version requires the 'pypdf' library (pip install pypdf).\n"
            "An input file is mandatory. Output defaults to [basename].minibook.pdf."
        )
    )
    
    # Optional positional arguments (infile, outfile)
    parser.add_argument('infile', nargs='?', default=None, help="Input PDF file.")
    # FIX: Corrected typo from parser.add.argument to parser.add_argument
    parser.add_argument('outfile', nargs='?', default=None, help="Output file ('-' for STDOUT).")
    
    # Flags
    parser.add_argument('-v', action='store_true', help="Produce status messages.")
    parser.add_argument('-vv', action='store_true', help="Produce debugging output.")
    
    args = parser.parse_args()
    
    # Check for input file and determine default output path
    if args.infile and args.outfile is None and args.infile != '-':
        basename = os.path.splitext(args.infile)[0]
        args.outfile = f"{basename}.minibook.pdf"
        
    run_minibook(args)

if __name__ == '__main__':
    # Try importing pypdf and exit if not found
    try:
        from pypdf import PdfReader, PdfWriter, Transformation, PaperSize, PageObject
    except ImportError:
        sys.stderr.write("\n--- Dependency Error ---\n")
        sys.stderr.write("The required Python library 'pypdf' is missing.\n")
        sys.stderr.write("Please install it via: pip install pypdf\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"An unexpected error occurred during import: {e}\n")
        sys.exit(1)
    
    main()

