import struct

# Assuming 'fin' is defined as a file object
fin = open('EGM08_REDNAP.GEM', 'rb')

if len > 0xa2:
    header, magic, fsiz, unk64, unk011 = struct.unpack("<9shIbb", fin.read(9 + 2 + 4 + 1 + 1))

fin.seek(18 + 53, 1)
a, f1, miny, minx, maxy, maxx, dx, dy, unk012, ave, ncol, nvals = struct.unpack("<ddddddddbfII", fin.read(8 + 8 + 8 + 8 + 8 + 8 + 8 + 8 + 1 + 4 + 4 + 4))

print header, a, f1, 'x', miny, minx, maxy, maxx, dx, dy, unk012, ave, ncol, nvals
nrow = nvals / ncol

print 'aaa', ncol, nrow
R2D = 180. / 3.14159265358979323846

for i in range(0, nrow * ncol):
    row = int(i / ncol)
    col = i % (ncol)
    val, = struct.unpack("h", fin.read(2))
    print val
    #print "%.9f %.9f %13.6f" % ((minx + col * dx) * R2D, (maxy - row * dy) * R2D, ave + val / 1000.)

fin.close()  # Close the file when done
