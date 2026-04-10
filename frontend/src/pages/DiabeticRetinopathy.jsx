import ScannerPage from '../components/ScannerPage';

export default function DiabeticRetinopathy() {
  return (
    <ScannerPage
      title="Diabetic Retinopathy Detection"
      badgeText="Ophthalmology AI Module"
      description="Upload fundus images for 5-level severity classification of diabetic retinopathy"
      formats=".jpg,.jpeg,.png,.bmp"
      endpoint="/api/v1/predict/retinopathy"
      moduleIcon="fas fa-eye"
      showEnsemble={true}
      showPatientLink={true}
    />
  );
}
