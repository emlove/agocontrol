LD     := g++

all: agotimer

agotimer: sunrise.o agotimer.o ../../devices/agozwave/CDataFile.o
	$(LD) -o $@ $(LDFLAGS) $^ -lqpidmessaging -lqpidtypes

clean:
	rm agotimer.o sunrise.o agotimer
