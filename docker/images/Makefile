
EGA_IMAGES=common db mq inbox worker cega_users cega_mq monitors frontend

all: $(EGA_IMAGES)

.PHONY: all $(EGA_IMAGES)

$(EGA_IMAGES):
	docker build -t nbis/ega:$@ $@

clean:
	docker images | awk '/none/{print $$3}' | while read n; do docker rmi $$n; done
