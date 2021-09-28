#!/bin/bash
DIR=`dirname "$0"`
OUTDIR="$DIR/htdocs"
if [ -d "$OUTDIR" ]; then
rm -R $OUTDIR
fi
mkdir -p $OUTDIR
wget -q -m -p -k -nH -P "$OUTDIR" http://localhost:8888
cp -R "$DIR/static" "$OUTDIR/"
