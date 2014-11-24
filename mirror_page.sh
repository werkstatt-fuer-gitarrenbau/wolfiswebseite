#!/bin/bash
DIR=`dirname "$0"`
OUTDIR="$DIR/htdocs"
mkdir -p $OUTDIR
wget -m -p -k -nH -P "$OUTDIR" http://localhost:8888
cp -R "$DIR/static" "$OUTDIR/"
