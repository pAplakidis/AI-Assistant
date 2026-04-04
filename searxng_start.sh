#sudo docker run --name searxng -d     -p 8888:8080     -v "./config/:/etc/searxng/"     -v "./data/:/var/cache/searxng/"     doc    ker.io/searxng/searxng:latest
docker run --name searxng -d \
  -p 8888:8080 \
  -v "/home/pavlos/searxng/config:/etc/searxng" \
  -v "/home/pavlos/searxng/data:/var/cache/searxng" \
  docker.io/searxng/searxng:latest
 
