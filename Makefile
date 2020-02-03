OWNER:=nielsbohr
NAME:=ssh-mount-dummy
TAG:=latest

all:	build

build:
	docker build --rm --force-rm -t $(OWNER)/$(NAME):$(TAG) .

push:
	docker push $(OWNER)/$(NAME):$(TAG)
