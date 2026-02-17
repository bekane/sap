obj-m += hello.o

KBUILD_CFLAGS += -g -O2


SRC = /lib/modules/$(shell uname -r)/build

all:
	make -C $(SRC) M=$(PWD) modules

clean:
	make -C $(SRC) M=$(PWD) clean


#make -C /lib/modules/$(uname -r)/build M=$PWD modules
