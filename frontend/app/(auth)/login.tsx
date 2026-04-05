import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Linking } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';

export default function LoginScreen() {
  const handleLogin = async () => {
    try {
      const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;
      // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
      const redirectUrl = `${BACKEND_URL}/(auth)/callback`;
      const authUrl = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
      
      await Linking.openURL(authUrl);
    } catch (error) {
      console.error('Login error:', error);
    }
  };

  return (
    <LinearGradient colors={['#0c0c0c', '#1a1a2e', '#16213e']} style={styles.container}>
      <View style={styles.content}>
        <View style={styles.header}>
          <Ionicons name="shield-checkmark" size={80} color="#3B82F6" />
          <Text style={styles.title}>CyberGuard Pro</Text>
          <Text style={styles.subtitle}>AI-Powered Predictive Intelligence</Text>
        </View>

        <View style={styles.features}>
          <FeatureItem icon="analytics" text="Real-time Analytics" />
          <FeatureItem icon="alert-circle" text="Smart Alerts" />
          <FeatureItem icon="trending-up" text="Risk Prediction" />
          <FeatureItem icon="eye" text="Anomaly Detection" />
        </View>

        <TouchableOpacity style={styles.loginButton} onPress={handleLogin}>
          <Ionicons name="logo-google" size={24} color="#fff" />
          <Text style={styles.loginButtonText}>Sign in with Google</Text>
        </TouchableOpacity>

        <Text style={styles.footer}>Secure authentication powered by Emergent</Text>
      </View>
    </LinearGradient>
  );
}

function FeatureItem({ icon, text }: { icon: any; text: string }) {
  return (
    <View style={styles.featureItem}>
      <Ionicons name={icon} size={24} color="#3B82F6" />
      <Text style={styles.featureText}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
    padding: 24,
    justifyContent: 'space-between',
  },
  header: {
    alignItems: 'center',
    marginTop: 80,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginTop: 16,
  },
  subtitle: {
    fontSize: 16,
    color: '#94a3b8',
    marginTop: 8,
  },
  features: {
    gap: 16,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    padding: 16,
    borderRadius: 12,
    gap: 12,
  },
  featureText: {
    fontSize: 16,
    color: '#fff',
  },
  loginButton: {
    backgroundColor: '#3B82F6',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 12,
    gap: 12,
    marginBottom: 16,
  },
  loginButtonText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
  },
  footer: {
    fontSize: 12,
    color: '#64748b',
    textAlign: 'center',
    marginBottom: 32,
  },
});
