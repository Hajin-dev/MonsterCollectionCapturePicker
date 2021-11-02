import sys, cv2, shutil, time, os
import numpy as np
from skimage.metrics import structural_similarity as compare_ssim
from PyQt5.QtWidgets import *
from PyQt5 import uic,QtCore

form_class = uic.loadUiType("./src/UI.ui")[0]
class MCS(QtCore.QThread,QtCore.QObject):
    result = QtCore.pyqtSignal(str)
    label = QtCore.pyqtSignal(str)
    pbar_value = QtCore.pyqtSignal(float)
    go_stop = QtCore.pyqtSignal(bool)
    def __init__(self,p1,p2,p3,st,c1,c2,parent=None):
        super(MCS,self).__init__(parent)
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.st = st
        self.c1 = c1
        self.c2 = c2
        self.thread_type = ''
        self.working = True
        self.go_stop.emit(True)
    def monster_search (self,sPath):
        source = cv2.imread(sPath,cv2.IMREAD_COLOR) # 검사 대상
        if source.shape[1]==1366:
            source = source[268:345,369:959] # 1366 * 768 에서 출력되는 위치 자르기
        elif source.shape[1]==800:
            source = source[100:177,86:676]
        elif source.shape[1]==1024:
            source = source[268:345,198:788]
        elif source.shape[1]==1280:
            source = source[220:297,326:916]
        elif source.shape[1]==1920:
            source = source[424:501,646:1236]
        else:
            print("지원되지 않는 형식!")
            return 0

        target = np.load('src//target.npy') # 탐색 목표 이미지
        mask = target[:,:,-1] #타겟의 알파 마스크 출력
        tmp,mask_r=cv2.threshold(mask,254,255,cv2.THRESH_BINARY) # tmp는 사용하지 않음, 유사 부울린 마스크(mask_r) 생성
        target = cv2.cvtColor(target,cv2.COLOR_RGBA2RGB)

        w,h=source.shape[:2]

        tgt = np.zeros((w,h,3),np.uint8)
        cv2.copyTo(target,mask_r,tgt)

        src = np.zeros((w,h,3),np.uint8)
        cv2.copyTo(source,mask_r,src)

        score , tmp = compare_ssim(src, tgt, full=True,multichannel=True)
        # full=True: 이미지 전체에 대해서 구조비교를 수행한다.
        return score * 100
    def file_list(self,root_dir,listbool):
        img_list = []
        img_name = ['.jpg', '.jpeg', '.JPG', '.PNG', '.png'] 
        if listbool == 2:
            for (root, dirs, files) in os.walk(root_dir):
                if len(files) > 0:
                    for file_name in files:
                        if file_name.startswith('Maple_A') and os.path.splitext(file_name)[1] in img_name:
                            img_path = root + "\\" + file_name
                            img_list.append(img_path)
        else : 
            for files in os.listdir(root_dir):
                if files.startswith('Maple_A') and '.'+files.split('.')[-1] in img_name:
                    img_path = root_dir + "\\" + files
                    img_list.append(img_path)                
        return(img_list)
    def run(self):
        timestr = time.strftime("%y-%m-%d_%H-%M-%S ")
        if self.thread_type =='class' and self.working:
            not_mon_log = "\n\n몬컬이 아닌 캡쳐 목록:"
            mon_log = "\n\n몬컬 캡처 목록:"
            cap_list = self.file_list(self.p1,self.c1)
            all_n = len(cap_list)
            i = 0
            for source in cap_list:
                filename = source.split('\\')[-1]
                score= self.monster_search(source)
                if score < self.st :
                    shutil.move(source,self.p2+'\\'+filename)
                    not_mon_log = not_mon_log+'\n'+filename+':'+f"{score:.1f}"+'%'
                else :
                    shutil.move(source,self.p3+'\\'+filename)
                    mon_log = mon_log+'\n'+filename+':'+f"{score:.1f}"+'%'
                i=i+1
                self.label.emit(f'{i}'+'/'+f'{all_n}')
                self.result.emit(filename+':'+f"{score:.1f}"+'%')
                self.pbar_value.emit((i+1)/all_n)
            if self.c2 :
                f = open(f"{os.getcwd()}\\log-{timestr}.txt",'w',encoding='UTF-8')
                f.write("시작시간: "+timestr+not_mon_log+mon_log)
                f.close()
            self.go_stop.emit(False)
        elif self.thread_type =='log' and self.working:
            not_mon_log = "\n\n몬컬이 아닌 캡쳐 목록:"
            mon_log = "\n\n몬컬 캡처 목록:"
            cap_list = self.file_list(self.p1,self.c1)
            all_n = len(cap_list)
            i = 0
            for source in cap_list:
                filename = source.split('\\')[-1]
                score= self.monster_search(source)
                if score < self.st :
                    not_mon_log = not_mon_log+'\n'+filename+':'+f"{score:.1f}"+'%'
                else :
                    mon_log = mon_log+'\n'+filename+':'+f"{score:.1f}"+'%'
                i=i+1
                self.label.emit(f'{i}'+'/'+f'{all_n}')
                self.result.emit(filename+':'+f"{score:.1f}"+'%')
                self.pbar_value.emit((i+1)/all_n)
            if self.c2 :
                f = open(f"{os.getcwd()}\\log-{timestr}.txt",'w',encoding='UTF-8')
                f.write("시작시간: "+timestr+not_mon_log+mon_log)
                f.close()
            self.go_stop.emit(False)
        else:
            self.terminate()
            self.quit()
class MyWindow(QMainWindow, form_class):
    path_signal = QtCore.pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.pushButton.clicked.connect(self.getFilepath1)
        self.pushButton_2.clicked.connect(self.getFilepath2)
        self.pushButton_3.clicked.connect(self.getFilepath3)
        
        self.pushButton_4.clicked.connect(self.classifying)
        self.pushButton_5.clicked.connect(self.logonly)
    def getFilepath1(self):
        path_name = QFileDialog.getExistingDirectory(self)
        self.lineEdit.setText(path_name)
        if path_name :
            self.pushButton_5.setEnabled(True)
        if self.lineEdit_3.text() and self.lineEdit_2.text() and self.lineEdit.text():
                self.pushButton_4.setEnabled(True)
    def getFilepath2(self):
        path_name = QFileDialog.getExistingDirectory(self)
        self.lineEdit_2.setText(path_name)
        if self.lineEdit_3.text() and self.lineEdit_2.text() and self.lineEdit.text():
            self.pushButton_4.setEnabled(True)
    def getFilepath3(self):
        path_name = QFileDialog.getExistingDirectory(self)
        self.lineEdit_3.setText(path_name)
        if self.lineEdit_3.text() and self.lineEdit_2.text() and self.lineEdit.text():
            self.pushButton_4.setEnabled(True)
    def classifying(self):

        self.progressBar.setEnabled(True)
        self.textEdit.setText("")
        
        check1 = self.checkBox.checkState()
        check2 = self.checkBox_2.checkState()
        p1 = self.lineEdit.text()
        p2 = self.lineEdit_2.text()
        p3 = self.lineEdit_3.text()
        st = self.spinBox.value()
        self.switch_widgets(True)
        self.th = MCS(p1,p2,p3,st,check1,check2,parent=self)
        self.th.result.connect(self.setResultBox)
        self.th.pbar_value.connect(self.pBarUpdate)
        self.th.label.connect(self.label5update)
        self.th.go_stop.connect(self.thread_stop)
        self.th.start()
        self.th.thread_type = 'class'
    def logonly(self):
        self.progressBar.setEnabled(True)
        self.textEdit.setText("")
        self.switch_widgets(True)

        check1 = self.checkBox.checkState()
        check2 = self.checkBox_2.checkState()
        p1 = self.lineEdit.text()
        st = self.spinBox.value()

        self.th = MCS(p1,'','',st,check1,check2,parent=self)
        self.th.result.connect(self.setResultBox)
        self.th.pbar_value.connect(self.pBarUpdate)
        self.th.label.connect(self.label5update)
        self.th.go_stop.connect(self.thread_stop)
        self.th.start()
        self.th.thread_type = 'log'
    def setResultBox(self, result):
        self.textEdit.append(result)
    def switch_widgets(self,onoff):
        if onoff:
            self.pushButton.setDisabled(True)
            self.pushButton_2.setDisabled(True)
            self.pushButton_3.setDisabled(True)
            self.pushButton_4.setDisabled(True)
            self.pushButton_5.setDisabled(True)
            self.checkBox.setDisabled(True)
            self.checkBox_2.setDisabled(True)
            self.spinBox.setDisabled(True)
        else:
            self.pushButton.setEnabled(True)
            self.pushButton_2.setEnabled(True)
            self.pushButton_3.setEnabled(True)
            if self.lineEdit_3.text() and self.lineEdit_2.text() and self.lineEdit.text():
                self.pushButton_4.setEnabled(True)            
            self.pushButton_5.setEnabled(True)
            self.checkBox.setEnabled(True)
            self.checkBox_2.setEnabled(True)
            self.spinBox.setEnabled(True)
    @QtCore.pyqtSlot(float)
    def pBarUpdate(self,val):
        self.progressBar.setValue(val*100)
    @QtCore.pyqtSlot(str)
    def label5update(self,val):
        self.label_5.setText(val)
    @QtCore.pyqtSlot(bool)
    def thread_stop(self,val):
        if val == False:
            self.th.terminate()
            self.th.working = False
            self.switch_widgets(False)
if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()