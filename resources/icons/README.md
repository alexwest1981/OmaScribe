# Ikoner

`*.svg` är [Lucide](https://lucide.dev) (lucide-static 1.52.0), licens **ISC** —
fri att använda och bädda in, även kommersiellt. Filerna är hämtade från
`https://unpkg.com/lucide-static@1.52.0/icons/<namn>.svg`.

De läses av `ui/icons.py`, som byter ut `currentColor` mot temats färg och
renderar dem i den storlek som efterfrågas. Vill du ha fler: hämta samma väg och
lägg filen här, så hittar `icon("<namn>")` den.
