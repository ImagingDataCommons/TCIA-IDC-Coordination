# NOTE: unset DCMDICTPATH if dictionary runtime issues

import os, sys, subprocess

patient_to_study_map_file = "/home/fedorov/gs/tcia-idc-datareviewcoordination/issue-1/PatientID_to_SeriesInstanceUID.csv"
patient_to_study_map_file = "/home/fedorov/gs/tcia-idc-datareviewcoordination/issue-1/1p19qDeletion_T2_series.csv"

conversion_command = "itkimage2segimage --inputImageList <Segmentation> --inputDICOMDirectory /home/fedorov/gs/gcs-public-data--healthcare-tcia-lgg-1p19qdeletion/dicom/<StudyUID>/<SeriesUID> --inputMetadata dcmqi_template.json --outputDICOM LGG-<PatientID>_seg.dcm"

segmentations_path_dash = "/home/fedorov/gs/tcia-idc-datareviewcoordination/issue-1/Revised_segmentations_from_Drive/<PatientID>/<PatientID>-Segmentation.nii.gz"
segmentations_path_underscore = "/home/fedorov/gs/tcia-idc-datareviewcoordination/issue-1/Revised_segmentations_from_Drive/<PatientID>/<PatientID>_Segmentation.nii.gz"

# those are the cases that failed during the initial attempt to convert
#failed_cases = ["223", "310", "326", "344", "348", "518", "525"]
#failed_cases = ["223"]

with open(patient_to_study_map_file,"r") as f:
    f.readline()
    for l in f:
        (patient_id,study_uid,series_uid) = l[:-1].split(",")[:3]
        # patient ID can be LGG-<number> or LGG_<number> - this is more robust
        patient_id = patient_id[-3:]

        print(patient_id)

        #if patient_id not in failed_cases:
        #    continue

        this_seg = None
        this_seg_path_dash = segmentations_path_dash.replace("<PatientID>","LGG-"+patient_id)
        this_seg_path_underscore = segmentations_path_underscore.replace("<PatientID>","LGG-"+patient_id)
        if os.path.exists(this_seg_path_dash):
            this_seg = this_seg_path_dash
        elif os.path.exists(this_seg_path_underscore):
            this_seg = this_seg_path_underscore
        else:
            print("ERROR: Cannot locate segmentations for LGG-"+patient_id)
            continue
        this_conversion_command = conversion_command.replace("<PatientID>", patient_id).replace("<StudyUID>", study_uid)
        print(this_conversion_command)
        this_conversion_command = this_conversion_command.replace("<SeriesUID>", series_uid)
        this_conversion_command = this_conversion_command.replace("<Segmentation>", this_seg)
        print(this_conversion_command)


        subprocess.run(this_conversion_command.split(" "))
        #break
