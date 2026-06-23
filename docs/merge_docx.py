import sys
from docx import Document
from docxcompose.composer import Composer


def main():
    if len(sys.argv) != 4:
        print("Usage: python merge_docx.py title.docx body.docx result.docx")
        sys.exit(1)

    title_path = sys.argv[1]
    body_path = sys.argv[2]
    output_path = sys.argv[3]

    master_document = Document(title_path)
    composer = Composer(master_document)

    body_document = Document(body_path)
    composer.append(body_document)

    composer.save(output_path)


if __name__ == "__main__":
    main()