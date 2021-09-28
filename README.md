

# vdl2readsb

Parses VDL2/ACARS message output of [dumpvdl2](https://github.com/szpajder/dumpvdl2) for useful information and converts it to SBS-like format, compatible with wiedehopf's [readsb](https://github.com/wiedehopf/readsb).

This is an experimental proof-of-concept. Please don't try to feed this data to any flight tracking websites!

The script tries to extract the following data:
 - registration and flight number in IATA format
 - latitude, longitude and altitude
 - departure and arrival airport codes, ETA.

### Input
JSON output of dumpvdl2

    {"vdl2": {"app": {"name": "dumpvdl2", "ver": "2.1.1"}, "t": {"sec": 1632024554, "usec": 194184}, "freq": 136975000, "burst_len_octets": 126, "hdr_bits_fixed": 0, "octets_corrected_by_fec": 0, "idx": 0, "sig_level": -27.208977, "noise_level": -45.464058, "freq_skew": -3.357008, "avlc": {"src": {"addr": "A7DB08", "type": "Aircraft", "status": "Airborne"}, "dst": {"addr": "10502A", "type": "Ground station"}, "cr": "Command", "frame_type": "I", "rseq": 1, "sseq": 0, "poll": false, "acars": {"err": false, "crc_ok": true, "more": false, "reg": ".N605NK", "mode": "2", "label": "12", "blk_id": "5", "ack": "!", "flight": "NK0626", "msg_num": "M80", "msg_num_seq": "A", "msg_text": "POSN 380202W 754933,-------,0409,3358,,- 43,29132  70,FOB  221,ETA 0710,KPHL,TJSJ,"}}}}

### Output
SBS-like CSV format with extra fields at the end (registration, flight, departure airport, arrival airport, eta)

    MSG,3,1,1,A7DB08,1,2021/09/19,04:09:14.194,2021/09/19,04:09:14.194,NK0626,,,,38.03389,-75.82583,,,,,,0,N605NK,NK0626,KPHL,TJSJ,0710

### Installation
- build and install [dumpvdl2](https://github.com/szpajder/dumpvdl2) with libacars and libzmq3-dev, make sure it can receive messages
- install [readsb](https://github.com/wiedehopf/readsb) and [tar1090](https://github.com/wiedehopf/tar1090)
- clone the repository and install python dependencies:
    
	    sudo apt install -y python3 python3-dev python3-pip
	    git clone https://github.com/Yura80/vdl2readsb.git
	    cd vdl2readsb
	    sudo pip install -r requirements.txt
    
- disable rtlsdr and enable SBS JAERO input port in /etc/default/readsb:

    ```NET_OPTIONS="--net --net-heartbeat 60 --net-ro-size 1250 --net-ro-interval 0.05 --net-ri-port 0 --net-ro-port 30002 --net-sbs-jaero-in-port 30003 --net-bi-port 30004,30104 --net-bo-port 30005 --net-sbs-in-port 33303"```
    
### Usage
- start dumpvdl2 (with your receiver's actual PPM correction value and frequencies for your region):
    
    ```dumpvdl2 --output decoded:json:zmq:mode=client,endpoint=tcp://127.0.0.1:5556 --rtlsdr 0 --gain 40 --correction 44 136975000 136650000 136700000 136800000 &```
    
- run this command to send messages to readsb and save to a local file:

    ```./vdl2readsb.py --input=zmq --out-tcp=localhost:33303 --out-file=./sbslog.txt &```
