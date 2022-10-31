import os
import json
from typing import List, Tuple
import numpy as np
import pandas as pd
import nibabel as nib
import SimpleITK as sitk
import cmapy
import random
import subprocess

class NiiSegHandler: 

    def __init__(self, nii_file_path, json_template_path, dic_color) -> None:
        self.nii_file_path = nii_file_path
        self.json_template =  json.loads(open(json_template_path, "r").read())
        self.nii_array = sitk.GetArrayFromImage(sitk.ReadImage(nii_file_path))
        self.nii_image = sitk.ReadImage(nii_file_path)
        self.anatomic_reg_dic = {'ABD' : {'CodeValue' : '818991007', #AnatomicRegionSequence
                                    'CodingSchemeDesignator': 'SCT', 
                                    'CodeMeaning' : 'abdominal lymph node'}, 
                                 'MED' : {'CodeValue' : '62683002',
                                    'CodingSchemeDesignator': 'SCT',
                                    'CodeMeaning' : 'mediastinal lymph node'}}
        self.dic_color = dic_color

    def create_json_metadata(self):
        temp_json = self.json_template.copy()
        temp_json['BodyPartExamined'] = 'ABDOMEN' if self.get_type_lymph() == 'ABD' else 'MEDIASTINUM' \
            if  self.get_type_lymph() == 'MED' else 'UKNOWN'
        nbr_labelsID = self.retrieve_labelID()[1:] 
        seg_dic = {}
        for id in nbr_labelsID: #labelID 0 is background
            seg = self.generate_segment_data(id)
            seg_dic[f"{id}"] = seg
        temp_json["segmentAttributes"][0] = list(seg_dic.values()) 
        print(temp_json)
        return temp_json 

    def generate_rd_color(self):
        pass

    def generate_segment_data(self, id):
        seg_attr = self.json_template['segmentAttributes'][0][0].copy()
        # seg_attr['AnatomicRegionSequence'] = self.anatomic_reg_dic['ABD'] \
        #     if self.get_type_lymph() == 'ABD' else self.anatomic_reg_dic['MED']
        seg_attr['recommendedDisplayRGBValue'] = self.dic_color[int(id)]#self.generate_rd_color()
        seg_attr['labelID'] = int(id)
        seg_attr['SegmentedPropertyTypeCodeSequence'] = self.anatomic_reg_dic['ABD'] \
            if self.get_type_lymph() == 'ABD' else self.anatomic_reg_dic['MED']
        seg_attr['SegmentDescription'] = f"Lymph node segmentation ID : {id}"
        return seg_attr

    def save_json_metadata(self, output_path) -> None:
        out_json = self.create_json_metadata()
        if not os.path.exists(output_path):
            subprocess.check_call("touch %s" % (str(output_path)), shell=True)
        else:
            subprocess.check_call("rm %s" % (str(output_path)), shell=True)
        with open(output_path, "w") as outfile:
            json.dump(out_json, outfile, indent = 4)

    def retrieve_labelID(self):
        return np.unique(self.nii_array)

    def convert_to_dcm(self, output_path_root, input_dcm_dir):
        #assume dcmqi is built
        if not os.path.exists(output_path_root):
            # !mkdir -p $output_path_root
            subprocess.check_call("mkdir -p %s" % (str(output_path_root)), shell=True)
        out_json_path = os.path.join(output_path_root, \
            self.nii_file_path.split('/')[-1][:-7]+"_metadata.json")
        self.save_json_metadata(out_json_path)
        out_dcm_path = os.path.join(output_path_root, self.nii_file_path.split('/')[-1][:-7]+".dcm")
        # subprocess.check_call("./script.ksh %s %s %s" % (arg1, str(arg2), arg3), shell=True)
        #path to dcmqi bin is fixed
        subprocess.check_call("/Users/ccosmin/Documents/IDC/git_issues/IDC-ProjectManagement/1373/git_packages/dcmqi-1.2.4-mac/bin/itkimage2segimage \
            --inputImageList %s \
            --inputDICOMDirectory %s \
            --outputDICOM %s \
            --inputMetadata %s \
            --verbose --skip" % (str(self.nii_file_path), str(input_dcm_dir), str(out_dcm_path), str(out_json_path)), shell=True)

    def get_shape(self):
        return np.shape(self.nii_array)

    def get_orientation(self):
        pass

    def get_type_lymph(self):
        return self.nii_file_path.split('/')[-1].split('_')[0]


