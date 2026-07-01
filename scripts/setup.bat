# Build a vector tile server (optional)
docker run -d --name mbtiles -p 8080:80 \
  -v "%cd%\data:/data" maptiler/tileserver-gl
