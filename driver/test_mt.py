#import sys
#sys.path.append('..\\..\\..\\')

import maitai

fw = maitai.MaiTai(2)
print fw.getWavelength()
print fw.getWavelengthRange()
fw.close()
#cam = pco.getCamera('pixelfly')
#cam.close()

