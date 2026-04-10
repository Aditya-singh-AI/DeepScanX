import ScannerPage from '../components/ScannerPage';

export default function BrainTumor() {
  return (
    <ScannerPage
      title="Brain Tumor Analysis"
      badgeText="Neurology AI Module"
      description="Upload brain MRI scans for AI-powered tumor detection and classification"
      formats=".jpg,.jpeg,.png,.bmp,.dcm,.dicom"
      endpoint="/api/v1/predict/brain"
      moduleIcon="fas fa-brain"
      showEnsemble={true}
      showPatientLink={true}
    />
  );
}
