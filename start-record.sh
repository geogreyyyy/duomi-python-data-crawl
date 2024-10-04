cid=$(docker ps -a| grep "python-data-record-run" |  awk '{print $1}')
if [ "$cid" != "" ]; then
        docker stop $cid
        docker rm $cid
fi
echo "docker ps id"
echo $cid
images=$(docker images| grep "python-data-record-run" | awk '{print $3}')
if [ "$images" != "" ]; then
        docker rmi $images
fi
docker build -t python-data-record-run:1.0 -f record-start/Dockerfile .

newimages=$(docker images| grep "python-data-record-run" | awk '{print $3}')

docker run -itd  --name python-data-record-run --network host  $newimages
