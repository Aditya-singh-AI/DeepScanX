import ScannerPage from '../components/ScannerPage';

export default function SkinCancer() {
  return (
    <ScannerPage
      title="Skin Cancer Detection"
      badgeText="Dermatology AI Module"
      description="Upload dermoscopy images to detect benign vs. malignant skin lesions using AI-powered analysis"
      formats=".jpg,.jpeg,.png,.bmp,.dcm,.dicom"
      endpoint="/api/v1/predict/skin"
      moduleIcon="fas fa-fingerprint"
      showEnsemble={true}
      showPatientLink={true}
    />
  );
}
