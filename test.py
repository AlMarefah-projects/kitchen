H=print
E=exit
import json as G,logging as F,torch,sys
from ultralytics import YOLO
def A():
	K='detection_model';J='yolo';C=True;F.basicConfig(level=F.INFO);A=F.getLogger(__name__)
	try:
		with open('config.json','r')as L:D=G.load(L)
		A.info('Configuration loaded successfully.')
	except FileNotFoundError:A.critical("Configuration file 'config.json' not found.",exc_info=C);E(1)
	except G.JSONDecodeError:A.critical("Error decoding JSON from 'config.json'.",exc_info=C);E(1)
	I='cuda'if torch.cuda.is_available()else'cpu';A.info(f"Using device: {I}")
	if D.get(J):B=D[J];A.info(f"Using YOLO model from: {B}")
	elif D.get(K):B=D[K];A.info(f"Using detection model from: {B}")
	else:B=D['model'];A.info(f"Using model from: {B}")
	try:M=YOLO(B,task='detect');A.info('Models loaded successfully.')
	except Exception as N:A.critical(f"Failed to load YOLO models: {N}",exc_info=C);E(1)
	O=M.predict(source='demo/demo-1.jpg',conf=.25,save=C,save_txt=C,save_conf=C,device=I)
	if O:H('Model inference successful.')
	else:H('Model inference failed.');E(1)
	return 0
if __name__=='__main__':B=A();sys.exit(B)