import ScannerPage from '../components/ScannerPage';

export default function BreastCancer() {
  return (
    <ScannerPage
      title="Breast Cancer Detection"
      badgeText="Oncology AI Module"
      description="Upload histopathology images to detect Invasive Ductal Carcinoma (IDC) using deep learning analysis"
      formats=".jpg,.jpeg,.png,.bmp"
      endpoint="/api/v1/predict/breast"
      moduleIcon="fas fa-heart-pulse"
      showEnsemble={true}
      showPatientLink={true}
    />
  );
}
