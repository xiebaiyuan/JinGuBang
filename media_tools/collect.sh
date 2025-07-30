#!/bin/bash
set +ex
## use to collect my files
function main {
    echo $1
    echo $2

    if [ -d $1 ] && [ -d $2 ]; then
        echo "Collect Files"
        if [ ! -d $2/pptxs ]; then
            mkdir $2/pptxs
        fi
        mv $1/*.pptx $2/pptxs
        mv $1/*.PPTX $2/pptxs

        if [ ! -d $2/pdfs ]; then
            mkdir $2/pdfs
        fi
        mv $1/*.pdf $2/pdfs

        if [ ! -d $2/txts ]; then
            mkdir $2/txts
        fi
        mv $1/*.txt $2/txts

        if [ ! -d $2/xlsxs ]; then
            mkdir $2/xlsxs
        fi
        mv $1/*.xlsx $2/xlsxs

        if [ ! -d $2/zips ]; then
            mkdir $2/zips
        fi
        mv $1/*.zip $2/zips

        if [ ! -d $2/keys ]; then
            mkdir $2/keys
        fi
        mv $1/*.key $2/keys

         if [ ! -d $2/docxs ]; then
            mkdir $2/docxs
        fi
        mv $1/*.docx $2/docxs 

        if [ ! -d $2/software ]; then
            mkdir $2/software
        fi
        mv $1/*.dmg $2/software
        mv $1/*.pkg $2/software

        if [ ! -d $2/others ]; then
            mkdir $2/others
        fi
        mv $1/* $2/others
    else
        echo "Directory $1 or $2 Not exists"
        exit 1
    fi




    exit 0
}
main "$@"