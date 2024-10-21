cid=$(docker ps -a| grep "python-data-crawl-run-my" |  awk '{print $1}')
if [ "$cid" != "" ]; then
        docker stop $cid
        docker rm $cid
fi
echo "docker ps id"
echo $cid
images=$(docker images| grep "python-data-crawl-run-my" | awk '{print $3}')
if [ "$images" != "" ]; then
        docker rmi $images
fi
docker build -t python-data-crawl-run-my:1.0 dockerfile-start/my/Dockerfile .

newimages=$(docker images| grep "python-data-crawl-run-my" | awk '{print $3}')

docker run -itd  --name python-data-crawl-run-my --network host  $newimages
