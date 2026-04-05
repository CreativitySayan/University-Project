import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function AlertsScreen() {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadAlerts();
  }, []);

  const loadAlerts = async () => {
    try {
      const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;
      const sessionToken = await AsyncStorage.getItem('session_token');
      
      const response = await fetch(BACKEND_URL + '/api/alerts?limit=100', {
        headers: {
          'Authorization': 'Bearer ' + sessionToken,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAlerts(data);
      }
    } catch (error) {
      console.error('Load alerts error:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const markAsRead = async (alertId: string) => {
    try {
      const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;
      const sessionToken = await AsyncStorage.getItem('session_token');
      
      await fetch(BACKEND_URL + '/api/alerts/' + alertId + '/read', {
        method: 'PATCH',
        headers: {
          'Authorization': 'Bearer ' + sessionToken,
        },
      });

      setAlerts(alerts.map(a => 
        a.alert_id === alertId ? { ...a, is_read: true } : a
      ));
    } catch (error) {
      console.error('Mark as read error:', error);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadAlerts();
  };

  const unreadCount = alerts.filter(a => !a.is_read).length;

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Alerts</Text>
          <Text style={styles.subtitle}>{unreadCount} unread alerts</Text>
        </View>
      </View>

      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#3B82F6" />
        }
      >
        {alerts.map((alert, index) => (
          <AlertCard key={index} alert={alert} onMarkRead={markAsRead} />
        ))}
        {alerts.length === 0 && (
          <View style={styles.emptyState}>
            <Ionicons name="notifications-off-outline" size={64} color="#64748b" />
            <Text style={styles.emptyText}>No alerts</Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function AlertCard({ alert, onMarkRead }: any) {
  const severityColor = {
    low: '#10B981',
    medium: '#F59E0B',
    high: '#EF4444',
    critical: '#DC2626',
  }[alert.severity] || '#64748b';

  const severityIcon = {
    low: 'information-circle',
    medium: 'warning',
    high: 'alert-circle',
    critical: 'nuclear',
  }[alert.severity] || 'alert';

  return (
    <TouchableOpacity
      style={[styles.alertCard, !alert.is_read && styles.alertCardUnread]}
      onPress={() => onMarkRead(alert.alert_id)}
    >
      <View style={[styles.alertIconContainer, { backgroundColor: severityColor + '20' }]}>
        <Ionicons name={severityIcon} size={32} color={severityColor} />
      </View>
      
      <View style={styles.alertContent}>
        <View style={styles.alertHeader}>
          <View style={[styles.severityBadge, { backgroundColor: severityColor }]}>
            <Text style={styles.severityText}>{alert.severity.toUpperCase()}</Text>
          </View>
          <Text style={styles.alertTime}>
            {new Date(alert.created_at).toLocaleDateString()}
          </Text>
        </View>
        
        <Text style={styles.alertType}>{alert.alert_type.replace('_', ' ').toUpperCase()}</Text>
        <Text style={styles.alertMessage}>{alert.message}</Text>
        
        {!alert.is_read && (
          <View style={styles.unreadDot} />
        )}
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0c0c0c',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    paddingTop: 8,
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
  scrollView: {
    flex: 1,
    padding: 16,
  },
  alertCard: {
    flexDirection: 'row',
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    gap: 12,
  },
  alertCardUnread: {
    borderLeftWidth: 4,
    borderLeftColor: '#3B82F6',
  },
  alertIconContainer: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
  },
  alertContent: {
    flex: 1,
    gap: 6,
  },
  alertHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  severityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  severityText: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#fff',
  },
  alertTime: {
    fontSize: 12,
    color: '#64748b',
  },
  alertType: {
    fontSize: 14,
    fontWeight: '600',
    color: '#94a3b8',
  },
  alertMessage: {
    fontSize: 14,
    color: '#fff',
  },
  unreadDot: {
    position: 'absolute',
    top: 0,
    right: 0,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#3B82F6',
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
    gap: 16,
  },
  emptyText: {
    fontSize: 16,
    color: '#64748b',
  },
});
