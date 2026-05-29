import { BarcodeScanningResult, CameraView, useCameraPermissions } from 'expo-camera';
import { useRef, useState } from 'react';
import { ActivityIndicator, Modal, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { getIngredientsByBarcode } from '../services/barcode_service';

const GREEN = '#2ECC71';
const GREEN_DARK = '#27AE60';

interface ProductResult {
  loading: boolean;
  productName?: string;
  ingredients?: string;
  error?: string;
}

export default function HomeScreen() {
  const [scanning, setScanning] = useState(false);
  const [permission, requestPermission] = useCameraPermissions();
  const [product, setProduct] = useState<ProductResult | null>(null);
  const scannedRef = useRef(false);

  const handleScan = async () => {
    if (!permission?.granted) {
      const result = await requestPermission();
      if (!result.granted) return;
    }
    scannedRef.current = false;
    setProduct(null);
    setScanning(true);
  };

  const handleBarcodeScanned = async ({ data }: BarcodeScanningResult) => {
    if (scannedRef.current) return;
    scannedRef.current = true;
    setScanning(false);
    setProduct({ loading: true });
    const result = await getIngredientsByBarcode(data);
    if (result.found) {
      setProduct({ loading: false, productName: result.productName, ingredients: result.ingredients });
    } else {
      setProduct({ loading: false, error: result.message });
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>AllergiScan</Text>
        <Text style={styles.subtitle}>Scan product ingredients to check for allergens</Text>
      </View>

      <View style={styles.center}>
        <Pressable
          style={({ pressed }) => [styles.scanButton, pressed && styles.scanButtonPressed]}
          onPress={handleScan}>
          <Text style={styles.scanText}>SCAN</Text>
        </Pressable>
        {product?.loading && (
          <View style={styles.resultBox}>
            <ActivityIndicator size="large" color={GREEN} />
          </View>
        )}
        {product && !product.loading && !product.error && (
          <ScrollView style={styles.resultBox} contentContainerStyle={styles.resultContent}>
            <Text style={styles.resultLabel}>Product</Text>
            <Text style={styles.resultValue}>{product.productName}</Text>
            <Text style={[styles.resultLabel, { marginTop: 12 }]}>Ingredients</Text>
            <Text style={styles.ingredientsText}>{product.ingredients}</Text>
          </ScrollView>
        )}
        {product?.error && (
          <View style={styles.resultBox}>
            <Text style={styles.errorText}>{product.error}</Text>
          </View>
        )}
      </View>

      <Modal visible={scanning} animationType="slide" statusBarTranslucent>
        <View style={styles.cameraContainer}>
          {permission?.granted ? (
            <CameraView
              style={StyleSheet.absoluteFill}
              facing="back"
              barcodeScannerSettings={{
                barcodeTypes: ['ean13', 'ean8', 'upc_a', 'upc_e', 'code128'],
              }}
              onBarcodeScanned={handleBarcodeScanned}>
              <SafeAreaView style={styles.cameraOverlay}>
                <Pressable style={styles.closeButton} onPress={() => setScanning(false)}>
                  <Text style={styles.closeText}>✕</Text>
                </Pressable>
                <View style={styles.scanFrame} />
                <Text style={styles.scanHint}>Point camera at barcode</Text>
              </SafeAreaView>
            </CameraView>
          ) : (
            <View style={styles.permissionContainer}>
              <Text style={styles.permissionText}>Camera access is needed to scan ingredients</Text>
              <Pressable style={styles.permissionButton} onPress={requestPermission}>
                <Text style={styles.permissionButtonText}>Allow Camera</Text>
              </Pressable>
              <Pressable onPress={() => setScanning(false)}>
                <Text style={styles.cancelText}>Cancel</Text>
              </Pressable>
            </View>
          )}
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  header: {
    paddingTop: 40,
    paddingHorizontal: 32,
    alignItems: 'center',
    gap: 8,
  },
  title: {
    fontSize: 32,
    fontWeight: '700',
    color: '#1A1A1A',
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: 15,
    color: '#888888',
    textAlign: 'center',
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scanButton: {
    width: 200,
    height: 200,
    borderRadius: 100,
    backgroundColor: GREEN,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: GREEN,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.4,
    shadowRadius: 20,
    elevation: 10,
  },
  scanButtonPressed: {
    backgroundColor: GREEN_DARK,
    transform: [{ scale: 0.96 }],
  },
  scanText: {
    fontSize: 28,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: 3,
  },
  cameraContainer: {
    flex: 1,
    backgroundColor: '#000',
  },
  cameraOverlay: {
    flex: 1,
    justifyContent: 'space-between',
    padding: 24,
  },
  closeButton: {
    alignSelf: 'flex-end',
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  closeText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '600',
  },
  scanFrame: {
    alignSelf: 'center',
    width: 280,
    height: 180,
    borderWidth: 2,
    borderColor: '#FFFFFF',
    borderRadius: 12,
    opacity: 0.7,
  },
  scanHint: {
    textAlign: 'center',
    color: '#FFFFFF',
    fontSize: 14,
    opacity: 0.8,
  },
  permissionContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
    gap: 16,
  },
  permissionText: {
    fontSize: 17,
    textAlign: 'center',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  permissionButton: {
    backgroundColor: GREEN,
    paddingHorizontal: 32,
    paddingVertical: 14,
    borderRadius: 12,
  },
  permissionButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  cancelText: {
    color: '#AAAAAA',
    fontSize: 16,
    paddingVertical: 14,
  },
  resultBox: {
    marginTop: 32,
    maxHeight: 300,
    width: '90%',
    backgroundColor: '#F4FBF7',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#D5EFE1',
  },
  resultContent: {
    padding: 20,
    alignItems: 'center',
    gap: 6,
  },
  resultLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#888888',
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
  resultValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1A1A1A',
    letterSpacing: 1,
  },
  ingredientsText: {
    fontSize: 14,
    color: '#444444',
    lineHeight: 20,
    textAlign: 'center',
  },
  errorText: {
    fontSize: 15,
    color: '#E74C3C',
    textAlign: 'center',
    padding: 20,
  },
});
