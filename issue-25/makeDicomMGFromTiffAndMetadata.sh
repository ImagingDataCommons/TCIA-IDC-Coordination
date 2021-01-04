#!/bin/sh

SRCDIR="CMMD_tif_and_ScannerDetailReference"
DSTDIR="CMMD_DICOM_MG"

TMPROOT=/tmp/`basename $0`.$$

STAMP=`date +%Y%m%d%H%M%S`.$$

for set in D1 D2
do
	subdirname="CMM${set}"
	metadatafilename="${subdirname}/${set}_meta.csv"
	lastsubject="NOSUBJECT"
	rm -rf "${DSTDIR}/CMM${set}"

	for tifdir in ${SRCDIR}/${subdirname}/${set}-[0-9]*
	do
		for tiffile in ${tifdir}/*.tif
		do
			subject=`basename "${tifdir}"`

			if [ "${subject}" = "${lastsubject}" ]
			then
				instancewithinseries=`expr $instancewithinseries + 1`
			else
				instancewithinseries=1
				if [ ! "${lastsubject}" = "NOSUBJECT" ]
				then
					#dctable -k StudyInstanceUID -k SeriesInstanceUID `find "${DSTDIR}/CMM${set}/${lastsubject}" -follow -name '*.dcm'`
					dcentvfy `find "${DSTDIR}/CMM${set}/${lastsubject}" -follow -name '*.dcm'`
				fi
			fi

			side=`basename "${tiffile}" | sed -e 's/^\([RL]\).*$/\1/'`

			# some files have two underscores (e.g., CMMD1/D1-1506/R__CC.tif) ...
			view=`basename "${tiffile}" | sed -e 's/^[RL][_]*\([A-Z]*\)[.].*$/\1/'`
			# handle error in file name of "CMMD1/D1-0920/L_C.tif"
			if [ "${view}" = "C" ]
			then
				view="CC"
			fi

			# some files have no entries in metadata when their sibling files (e.g., side with pathology) do, so use to get age, year
			# also get rid of control characters (e.g., trailing new line)
			subjectmetadata=`grep "${subject}" "${SRCDIR}/${metadatafilename}" | head -1 | tr -d '\n\r'`
			filemetadata=`grep "${subject},${side}" "${SRCDIR}/${metadatafilename}" | tr -d '\n\r'`

			#ID,LeftRight,Age,yr,number,abnormality,classification
			#D1-0001,R,44,2014,2,calcification,Benign

			#ID,LeftRight,Age,yr,number,abnormality,classification,subtype
			#D2-0001,L,64,2015,2,Calcification,Malignant,Luminal B

			age=`echo "${subjectmetadata}" | awk -F, '{print $3}'`

			year=`echo "${subjectmetadata}" | awk -F, '{print $4}'`
			# some subjects missing year, e.g., CMMD1/D1-1357
			if [ -z "${year}" ]
			then
				year="1901"
			fi

			echo "Doing subject ${subject} age ${age} year ${year} side ${side} view ${view} instancewithinseries ${instancewithinseries} file ${tiffile} using subjectmetadata ${subjectmetadata} and filemetadata ${filemetadata}"

			tiffsize=`tiffinfo "${tiffile}" | grep 'Image Width' | sed -e 's/^.*Image Width: \([0-9]*\).* Image Length: \([0-9]*\).*$/\1 \2/'`
			if [ "${tiffsize}" = "1914 2294" ]
			then
				#echo ":${tiffsize}: match GE size"
				imagerpixelspacing="0.094090909"
			else
				echo ":${tiffsize}: does not match GE size"
				imagerpixelspacing="0"
			fi

			#almost all 8 bits; exception is CMMD1/D1-1343/L_CC.tif, which is 16 bits
			bitspersample=`tiffinfo "${tiffile}" | grep 'Bits/Sample' | sed -e 's/^.*Bits.Sample: \([0-9]*\).*$/\1/'`
			if [ "${bitspersample}" = "8" ]
			then
				tifftopnmoptions=""
				pnmtodcmoptions=""
				windowcenter="128"
				windowwidth="256"
			elif [ "${bitspersample}" = "16" ]
			then
				# byrow option is necessary else says "actual resolution has been reduced to 24 bits per pixel in the conversion"
				tifftopnmoptions="-byrow "
				# PNM utilities byte order is big (regardless of what TIFF was)
				pnmtodcmoptions="-big "
				windowcenter="32768"
				windowwidth="65536"
			fi

			patientorientation=" "
			if [ "${view}" = "CC" ]
			then
				if [ "${side}" = "L" ]
				then
					patientorientation="A\\R"
				elif [ "${side}" = "R" ]
				then
					patientorientation="P\\L"
				fi
			elif [ "${view}" = "MLO" ]
			then
				if [ "${side}" = "L" ]
				then
					patientorientation="A\\FR"
				elif [ "${side}" = "R" ]
				then
					patientorientation="P\\FL"
				fi
			fi

			rm -rf ${TMPROOT}*

			tifftopnm -quiet ${tifftopnmoptions} "${tiffile}" >"${TMPROOT}.pnm"
			# make DigitalMammographyXRayImageStorageForPresentation
			# use stamp argument to assure Study and Series UIDs are shared as necessary
			pnmtodc -nodisclaimer \
				${pnmtodcmoptions} \
				-stamp "${STAMP}" \
				-r PatientName "${subject}^" \
				-r PatientID "${subject}" \
				-r PatientAge "0${age}Y" \
				-r PatientSex "F" \
				-r ImageLaterality "${side}" \
				-r StudyDate "${year}0101" \
				-r StudyTime "000000" \
				-r SeriesDate "${year}0101" \
				-r SeriesTime "000000" \
				-r ContentDate "${year}0101" \
				-r ContentTime "000000" \
				-r AcquisitionDate "${year}0101" \
				-r AcquisitionTime "000000" \
				-r StudyID "${subject}_${year}" \
				-r SeriesNumber "1" \
				-r InstanceNumber ${instancewithinseries} \
				-r Modality "MG" \
				-r SOPClassUID "1.2.840.10008.5.1.4.1.1.1.2" \
				-r PresentationIntentType "FOR PRESENTATION" \
				-r ImageType "DERIVED\\PRIMARY" \
				-r PixelIntensityRelationship "LOG" \
				-r PixelIntensityRelationshipSign " -1" \
				-r RescaleIntercept "0" \
				-r RescaleSlope "1" \
				-r RescaleType "US" \
				-r WindowCenter "${windowcenter}" \
				-r WindowWidth "${windowwidth}" \
				-r VOILUTFunction "SIGMOID" \
				-r WindowCenterWidthExplanation "Full width of 8 bit data" \
				-r PresentationLUTShape "IDENTITY" \
				-r LossyImageCompression "00" \
				-r BurnedInAnnotation "NO" \
				-r DerivationDescription "Converted to 8 bit" \
				-r DetectorType "SCINTILLATOR" \
				-r PositionerType "MAMMOGRAPHIC" \
				-r OrganExposed "BREAST" \
				-r ImagerPixelSpacing "${imagerpixelspacing}\\${imagerpixelspacing}" \
				-r AcquisitionContextSequence " " \
				-r PatientOrientation "${patientorientation}" \
				-d NumberOfFrames \
				-d ConversionType \
				"${TMPROOT}.pnm" "${TMPROOT}_beforemetadata.dcm"

			rm -rf "${TMPROOT}_addanatomicregion.dcm"
			# SRT: T-04000
			ancreate <<EOF >"${TMPROOT}_addanatomicregion.dcm"
(0x0008,0x2218) SQ Anatomic Region Sequence    VR=<SQ>   VL=<0xffffffff>      []
%item
(0x0008,0x0100) SH Code Value    VR=<SH>   VL=<0x0008>  <76752008>
(0x0008,0x0102) SH Coding Scheme Designator      VR=<SH>   VL=<0x0004>  <SCT>
(0x0008,0x0104) LO Code Meaning          VR=<LO>   VL=<0x0006>  <Breast>
%enditem
%endseq
EOF
			dcmerge -nodisclaimer "${TMPROOT}_beforemetadata.dcm" "${TMPROOT}_addanatomicregion.dcm" -of "${TMPROOT}_withanatomicregion.dcm"

			rm -rf "${TMPROOT}_addviewtmp.dcm"
			if [ "${view}" = "CC" ]
			then
				# SRT: R-10242
				ancreate <<EOF >"${TMPROOT}_addviewtmp.dcm"
(0x0054,0x0220) SQ View Code Sequence    VR=<SQ>   VL=<0xffffffff>      []
%item
(0x0008,0x0100) SH Code Value    VR=<SH>   VL=<0x000a>  <399162004 >
(0x0008,0x0102) SH Coding Scheme Designator      VR=<SH>   VL=<0x0004>  <SCT>
(0x0008,0x0104) LO Code Meaning          VR=<LO>   VL=<0x000e>  <cranio-caudal >
(0x0054,0x0222) SQ View Modifier Code Sequence   VR=<SQ>   VL=<0xffffffff>      []
%endseq
%enditem
%endseq
EOF
			elif [ "${view}" = "MLO" ]
			then
				# SRT: R-10226
				ancreate <<EOF >"${TMPROOT}_addviewtmp.dcm"
(0x0054,0x0220) SQ View Code Sequence    VR=<SQ>   VL=<0xffffffff>      []
%item
(0x0008,0x0100) SH Code Value    VR=<SH>   VL=<0x000a>  <399368009 >
(0x0008,0x0102) SH Coding Scheme Designator      VR=<SH>   VL=<0x0004>  <SCT>
(0x0008,0x0104) LO Code Meaning          VR=<LO>   VL=<0x0016>  <medio-lateral oblique >
(0x0054,0x0222) SQ View Modifier Code Sequence   VR=<SQ>   VL=<0xffffffff>      []
%endseq
%enditem
%endseq
EOF
			fi
			if [ -f "${TMPROOT}_addviewtmp.dcm" ]
			then
				dcmerge -nodisclaimer -tiff "${TMPROOT}_withanatomicregion.dcm" "${TMPROOT}_addviewtmp.dcm" -of "${TMPROOT}_withview.dcm"
			else
				mv "${TMPROOT}_withanatomicregion.dcm" "${TMPROOT}_withview.dcm"
			fi

			#dctable -decimal -k Rows -k Columns "${TMPROOT}_withview.dcm"
			#dciodvfy -profile IHEMammo "${TMPROOT}_withview.dcm"
			dciodvfy "${TMPROOT}_withview.dcm"
			#tiffinfo "${TMPROOT}_withview.dcm"

			mkdir -p "${DSTDIR}/CMM${set}/${subject}"
			cp "${TMPROOT}_withview.dcm" "${DSTDIR}/CMM${set}/${subject}/${side}_${view}.dcm"

			lastsubject="${subject}"
		done
	done
done
