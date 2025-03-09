INSTALLDIR="/usr/local/"
sudo mkdir -p "$INSTALLDIR/include/cmixins/"
sudo cp -rv system/* "$INSTALLDIR/include/cmixins/"
sudo cp -v cm-2 "$INSTALLDIR/bin/cmixins"
