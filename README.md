# Minibook

A Python tool to convert any PDF file into a miniature booklet format.

## Requirements

*   Python 3
*   [pypdf](https://pypi.org/project/pypdf/)

## Installation

1.  Clone this repository.
2.  Install the required dependency:

    ```bash
    pip install pypdf
    ```

## Usage

Run the script on a PDF file:

```bash
python minibook.py input.pdf [output.pdf]
```

If the output filename is not specified, it defaults to `[basename].minibook.pdf`.

## Printing & Assembly Instructions

To ensure the booklet is formed correctly, follow these steps exactly:

1.  **Printing**:
    *   Select **Double-sided (Duplex)** printing.
    *   Choose **Flip on Long Edge** (Binding on Long Edge).
    *   Ensure **No Rotation** is applied by the printer settings (e.g., disable "Auto-rotate and center" if it interferes with the layout).

2.  **Assembly**:
    *   Make a **horizontal cut** across the middle of the stack of pages (separating the top halves from the bottom halves).
    *   Take the bottom half stack and **fold it under** the top half stack along the cut line. The two halves of the *back of the last page* should be facing each other.
    *   Fold the stack in half vertically and staple along the fold (saddle stitch).

## License

MIT License

Copyright (c) 2001-2026 Jason Karcz

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
