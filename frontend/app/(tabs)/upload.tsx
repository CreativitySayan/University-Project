import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator, Alert, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as DocumentPicker from 'expo-document-picker';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function UploadScreen() {
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleUpload = async () => {
    try {
      const doc = await DocumentPicker.getDocumentAsync({
        type: ['text/csv', 'application/json'],
      });

      if (doc.canceled) return;

      setUploading(true);
      const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;
      const sessionToken = await AsyncStorage.getItem('session_token');

      const formData = new FormData();
      formData.append('file', {
        uri: doc.assets[0].uri,
        name: doc.assets[0].name,
        type: doc.assets[0].mimeType || 'application/octet-stream',
      } as any);

      const response = await fetch(BACKEND_URL + '/api/upload', {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer ' + sessionToken,
        },
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setResult(data);
        Alert.alert('Success', 'Dataset uploaded and processed successfully!');
      } else {
        const error = await response.json();
        Alert.alert('Error', error.detail || 'Upload failed');
      }
    } catch (error: any) {
      console.error('Upload error:', error);
      Alert.alert('Error', error.message || 'Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <Text style={styles.title}>Upload Dataset</Text>
          <Text style={styles.subtitle}>Upload CSV or JSON complaint data</Text>
        </View>

        <View style={styles.uploadArea}>
          <Ionicons name="cloud-upload-outline" size={80} color="#3B82F6" />
          <Text style={styles.uploadText}>Upload your complaint dataset</Text>
          <Text style={styles.uploadSubtext}>Supports CSV and JSON formats</Text>
          
          <TouchableOpacity
            style={styles.uploadButton}
            onPress={handleUpload}
            disabled={uploading}
          >
            {uploading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <>
                <Ionicons name="document" size={20} color="#fff" />
                <Text style={styles.uploadButtonText}>Choose File</Text>
              </>
            )}
          </TouchableOpacity>
        </View>

        {result && (
          <View style={styles.resultCard}>
            <Text style={styles.resultTitle}>Upload Results</Text>
            <ResultItem label="Total Records" value={result.total_records} />
            <ResultItem label="Complaints Created" value={result.complaints_created} />
            <ResultItem label="Predictions Generated" value={result.predictions_created} />
            <ResultItem label="Alerts Created" value={result.alerts_created} />
          </View>
        )}

        <View style={styles.infoCard}>
          <Text style={styles.infoTitle}>Required Columns:</Text>
          <View style={styles.columnList}>
            <ColumnItem text="complaint_id" />
            <ColumnItem text="complaint_time" />
            <ColumnItem text="complaint_type" />
            <ColumnItem text="location" />
            <ColumnItem text="description" />
            <ColumnItem text="status" />
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

function ResultItem({ label, value }: { label: string; value: number }) {
  return (
    <View style={styles.resultItem}>
      <Text style={styles.resultLabel}>{label}</Text>
      <Text style={styles.resultValue}>{value}</Text>
    </View>
  );
}

function ColumnItem({ text }: { text: string }) {
  return (
    <View style={styles.columnItem}>
      <Ionicons name="checkmark-circle" size={16} color="#10B981" />
      <Text style={styles.columnText}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0c0c0c',
  },
  content: {
    padding: 16,
  },
  header: {
    marginBottom: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
  },
  subtitle: {
    fontSize: 14,
    color: '#94a3b8',
    marginTop: 4,
  },
  uploadArea: {
    backgroundColor: '#1a1a2e',
    borderRadius: 16,
    padding: 32,
    alignItems: 'center',
    borderWidth: 2,
    borderStyle: 'dashed',
    borderColor: '#3B82F6',
    gap: 16,
  },
  uploadText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
  },
  uploadSubtext: {
    fontSize: 14,
    color: '#94a3b8',
  },
  uploadButton: {
    flexDirection: 'row',
    backgroundColor: '#3B82F6',
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 12,
    gap: 8,
    alignItems: 'center',
    marginTop: 16,
  },
  uploadButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  resultCard: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    marginTop: 24,
    gap: 12,
  },
  resultTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 8,
  },
  resultItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  resultLabel: {
    fontSize: 14,
    color: '#94a3b8',
  },
  resultValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#3B82F6',
  },
  infoCard: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    marginTop: 24,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 12,
  },
  columnList: {
    gap: 8,
  },
  columnItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  columnText: {
    fontSize: 14,
    color: '#94a3b8',
    fontFamily: 'monospace',
  },
});
