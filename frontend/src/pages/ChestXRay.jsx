import ScannerPage from '../components/ScannerPage';

export default function ChestXRay() {
  return (
    <ScannerPage
      title="Chest X-Ray Analysis"
      badgeText="Radiology AI Module"
      description="Upload standard chest X-ray images to detect Pneumonia, COVID-19, and Tuberculosis"
      formats=".jpg,.jpeg,.png,.bmp,.dcm,.dicom"
      endpoint="/api/v1/predict/chest"
      moduleIcon="fas fa-x-ray"
      showEnsemble={true}
      showPatientLink={true}
    />
  );
}
