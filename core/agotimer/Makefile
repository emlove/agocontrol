LD     := g++

all: agotimer

agotimer: sunrise.o agotimer.o ../../shared/CDataFile.o
	$(LD) -o $@ $(LDFLAGS) $^ -lqpidmessaging -lqpidtypes

.PHONY: clean
clean:
	rm -f agotimer.o sunrise.o agotimer
