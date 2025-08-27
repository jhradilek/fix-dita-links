# dita-cleanup

**dita-cleanup** is a command-line utility that allows you to clean up DITA topics after conversion from AsciiDoc.

In combination with [asciidoctor-dita-vale](https://github.com/jhradilek/asciidoctor-dita-vale), [asciidoctor-dita-topic](https://github.com/jhradilek/asciidoctor-dita-topic), and [dita-convert](https://github.com/jhradilek/dita-custom-xslt/), this project can be used to rapidly convert AsciiDoc content to DITA:

1.  Identify incompatible markup in the AsciiDoc source file:

    ```console
    vale source_file.adoc
    ```
2.  Convert the AsciiDoc file to a generic DITA topic:

    ```console
    asciidoctor -r dita-topic -b dita-topic -S secure source_file.adoc
    ```
3.  Convert the generic DITA topic to a specialized DITA concept, reference, or task:

    ```console
    dita-convert -g source_file.dita -o output_file.dita
    ```

4.  Clean up the resulting DITA file:

    ```console
    dita-cleanup -iI -D ../images -X . output_file.dita
    ```

## Installation

Install the `dita-cleanup` Python package:

```
python3 -m pip install --upgrade dita-cleanup
```

## Usage

*   Remove unresolved [AsciiDoc attribute references](https://docs.asciidoctor.org/asciidoc/latest/attributes/reference-attributes/#reference-custom) from element IDs:

    ```console
    dita-cleanup --prune-ids *.dita
    ```
*   Remove unresolved [AsciiDoc include directives](https://docs.asciidoctor.org/asciidoc/latest/directives/include/):

    ```console
    dita-cleanup --prune-includes *.dita
    ```
*   Replace unresolved [AsciiDoc attribute references](https://docs.asciidoctor.org/asciidoc/latest/attributes/reference-attributes/#reference-custom) with reusable content references:

    ```console
    dita-cleanup --conref-target 'topic.dita#topic-id' *.dita
    ```
*   Add a directory path to all image references:

    ```console
    dita-cleanup --images-dir ../images/ *.dita
    ```
*   Update invlid cross references based on DITA files present in the supplied directory:

    ```console
    dita-cleanup --xref-dir . *.dita
    ```

*   Print the updates to standard output instead of overwriting the supplied files:

    ```console
    dita-cleanup --prune-ids --output - *.dita
    ```

*   For a complete list of available command-line options and their short versions, run `dita-cleanup` with the `--help` option:

    ```console
    dita-cleanup --help
    ```

## Copyright

Copyright © 2025 Jaromir Hradilek

This program is free software, released under the terms of the MIT license. It is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
