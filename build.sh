docker build . -t moreai:latest

docker save -o image.tar moreai:latest

scp image.tar gilfoyle@prmed.az:/home/gilfoyle
