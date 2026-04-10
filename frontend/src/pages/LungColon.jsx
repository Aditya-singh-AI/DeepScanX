import ScannerPage from '../components/ScannerPage';

export default function LungColon() {
  return (
    <ScannerPage
      title="Lung & Colon Detection"
      badgeText="Pulmonology AI Module"
      description="Upload histopathology images to classify lung and colon tissue across 5 categories using AI-powered analysis"
      formats=".jpg,.jpeg,.png,.bmp,.dcm,.dicom"
      endpoint="/api/v1/predict/lung"
      moduleIcon="fas fa-lungs"
      showEnsemble={true}
      showPatientLink={true}
    />
  );
}
