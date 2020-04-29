import os
import SimpleITK
import re
import shutil

import common
def attach_image_info(I, orig:list, spac:list, size:list, dirc:list):
    orig.append(I.GetOrigin())
    spac.append(I.GetSpacing())
    size.append(I.GetSize())
    dirc.append(I.GetDirection())

def Transform(inputIm:SimpleITK.Image,refImage:SimpleITK.Image)->SimpleITK.Image:

   
    t = SimpleITK.TranslationTransform(3, [0, 0, 0])
    t.SetIdentity()
    
    resampler = SimpleITK.ResampleImageFilter()
    resampler.SetReferenceImage(refImage)
    resampler.SetInterpolator(SimpleITK.sitkNearestNeighbor)
    resampler.SetTransform(t)
    I = resampler.Execute(inputIm)
    return I

def print_image_info(img_l:list, sg_l:list):
    orig = []
    spac = []
    size = []
    dirc = []
    names = []
    for im in img_l:
        reader = SimpleITK.ImageSeriesReader()
        dicom_names = reader.GetGDCMSeriesFileNames( im )
        if len(dicom_names)>1:
            name = os.path.basename(im)
            reader.SetFileNames(dicom_names)
            I = reader.Execute()
            attach_image_info(I, orig, spac, size, dirc)
            names.append(name)
    I = SimpleITK.ReadImage(sg_l[0])
    attach_image_info(I, orig, spac, size, dirc)
    names.append(os.path.basename(sg_l[0]))
    str_or = 'Orig: \n'
    str_sp = 'Spac: \n'
    str_sz = 'Size: \n'
    str_di = 'Dirc: \n'
    for i in range(0, len(names)):
        str_or +='\t{}:\t\t{}\n'.format(names[i],orig[i])
        str_sp +='\t{}:\t\t{}\n'.format(names[i],spac[i])
        str_sz +='\t{}:\t\t{}\n'.format(names[i],size[i])
        str_di +='\t{}:\t\t{}\n'.format(names[i],dirc[i])
    print('{}\n{}\n{}\n{}'.format(str_or,str_sp,str_sz,str_di))


input_img_folder = '/Users/afshin/Dropbox (Partners HealthCare)/IDC-MF_DICOM/SegOrientation/C4KC-KiTS/KiTS-{:05d}'
seg2im_exe = '/Users/afshin/Documents/work/QIICR/bin/bin/segimage2itkimage'
im2seg_exe = '/Users/afshin/Documents/work/QIICR/bin/bin/itkimage2segimage'
dynamic_lib = '/Users/afshin/Documents/softwares/dcmtk/3.6.5/bin/lib'
out_folder = '/Users/afshin/Documents/work/SegOrientation/Output'
if os.path.exists(out_folder):
    shutil.rmtree(out_folder)
os.makedirs(out_folder)
out_file_common_name = 'tmp'
output_folder = ''
i = 2
dcm_img_fun = lambda x: x.endswith('.dcm') and 'arterial' in x
dcm_seg_fun = lambda x: x.endswith('.dcm') and 'Segmentation' in x
dcmimg_list =[]
dcmseg_list =[]
common.recursive_find(input_img_folder.format(i),dcmimg_list, dcm_img_fun, True)
common.recursive_find(input_img_folder.format(i),dcmseg_list, dcm_seg_fun, False)
dicom_folder = dcmimg_list[0]
dicom_seg_file = dcmseg_list[0]

seg2im_params = [seg2im_exe, '--outputDirectory', out_folder ,
            '-t', 'nii','-p', out_file_common_name, '--inputDICOM',dicom_seg_file]
common.RunExe(seg2im_params,
            os.path.join(out_folder,'err_.txt'),os.path.join(out_folder,'out_.txt'),[],
            {"DYLD_LIBRARY_PATH":dynamic_lib})
sg_list =[]
sgfun = lambda x: re.match('.*{}.*.nii.gz'.format(out_file_common_name),x) is not None
common.recursive_find(out_folder,sg_list, sgfun, False)
transformed_files = ''
seg_json_file = os.path.join(out_folder,'{}-meta.json'.format(out_file_common_name))
seg_file_pattern = os.path.join(out_folder,'{}-{{}}.nii.gz'.format(out_file_common_name))
n = 1
seg_file = seg_file_pattern.format(n)
while os.path.exists(seg_file):
    niix_sg = SimpleITK.ReadImage(seg_file)
    reader = SimpleITK.ImageSeriesReader()
    dicom_names = reader.GetGDCMSeriesFileNames( dicom_folder )
    reader.SetFileNames(dicom_names)
    dicom_im = reader.Execute()
    transformed_seg = Transform(niix_sg, dicom_im)
    transformed_seg_file = seg_file.replace('tmp','transformed')
    if len(transformed_files)==0:
        transformed_files = transformed_seg_file
    else:
        transformed_files +=',{}'.format(transformed_seg_file)
    SimpleITK.WriteImage(transformed_seg, transformed_seg_file, True)
    n +=1
    seg_file = seg_file_pattern.format(n)

final_dicom_file = os.path.join(out_folder,'final_.dcm')
im2seg_params = [im2seg_exe, '--inputImageList', transformed_files, '--inputDICOMDirectory', dicom_folder,
  '--outputDICOM', final_dicom_file, '--inputMetadata', seg_json_file ]
common.RunExe(im2seg_params,
            os.path.join(out_folder,'err_.txt'),os.path.join(out_folder,'out_.txt'),[],
            {"DYLD_LIBRARY_PATH":dynamic_lib})



