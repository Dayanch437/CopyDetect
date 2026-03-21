import { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import {
  ConfigProvider,
  Layout,
  Card,
  Segmented,
  Input,
  Upload,
  Button,
  Spin,
  Typography,
  Space,
  Row,
  Col,
  Divider,
  Progress,
  Tag,
  App as AntApp,
  theme as antTheme,
} from 'antd';
import {
  FileTextOutlined,
  UploadOutlined,
  SafetyOutlined,
  WarningOutlined,
  FileProtectOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const MAX_FILE_SIZE_MB = 10;
const POLL_INTERVAL_MS = 5000;
const MAX_POLL_ATTEMPTS = 60;

const { TextArea } = Input;
const { Content, Header } = Layout;
const { Title, Text } = Typography;

// ─── Header ──────────────────────────────────────────────────────────────────

function AppHeader() {
  return (
    <Header
      style={{
        background: '#0b1120',
        borderBottom: '1px solid #1e2d45',
        padding: '0 32px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        height: '60px',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}
    >
      <Space size={10}>
        <FileProtectOutlined style={{ fontSize: '22px', color: '#4f8ef7' }} />
        <Text
          strong
          style={{ fontSize: '17px', color: '#e2e8f0', letterSpacing: '0.4px' }}
        >
          CopyDetect
        </Text>
      </Space>
      <Tag
        color="blue"
        style={{ fontSize: '10px', letterSpacing: '1px', fontWeight: 600 }}
      >
        BETA
      </Tag>
    </Header>
  );
}

// ─── Upload Area (shared) ─────────────────────────────────────────────────────

function UploadArea({ label, accentColor, file, onSet }) {
  const { message } = AntApp.useApp();

  const beforeUpload = (f) => {
    const validTypes = ['.pdf', '.docx', '.txt'];
    const ext = f.name.slice(f.name.lastIndexOf('.')).toLowerCase();
    if (!validTypes.includes(ext)) {
      message.error('Diňe PDF, DOCX we TXT faýllary goldanylýar.');
      return Upload.LIST_IGNORE;
    }
    if (f.size / 1024 / 1024 > MAX_FILE_SIZE_MB) {
      message.error(`Faýl ${MAX_FILE_SIZE_MB} MB-dan kiçi bolmalydyr.`);
      return Upload.LIST_IGNORE;
    }
    onSet(f);
    return false;
  };

  return (
    <Card
      size="small"
      title={
        <Space size={8}>
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: accentColor,
              display: 'inline-block',
              flexShrink: 0,
            }}
          />
          <Text
            style={{
              color: '#94a3b8',
              fontSize: '11px',
              textTransform: 'uppercase',
              letterSpacing: '1px',
              fontWeight: 700,
            }}
          >
            {label}
          </Text>
        </Space>
      }
      styles={{
        body: { padding: '16px' },
        header: { borderBottom: '1px solid #1e2d45', minHeight: '44px' },
      }}
      style={{ background: '#0d1626', border: '1px solid #1e2d45', borderRadius: '12px' }}
    >
      <Upload
        beforeUpload={beforeUpload}
        onRemove={() => onSet(null)}
        maxCount={1}
        accept=".pdf,.docx,.txt"
        showUploadList={!!file}
      >
        <div
          style={{
            border: `2px dashed ${file ? accentColor : '#2a3a55'}`,
            borderRadius: '10px',
            padding: '44px 20px',
            textAlign: 'center',
            cursor: 'pointer',
            transition: 'all 0.2s',
            background: file ? `${accentColor}0d` : 'transparent',
          }}
        >
          <UploadOutlined
            style={{
              fontSize: '28px',
              color: file ? accentColor : '#3a4f6e',
              marginBottom: '10px',
              display: 'block',
            }}
          />
          <Text style={{ color: '#94a3b8', fontSize: '14px', display: 'block' }}>
            {file ? file.name : 'Faýly saýlaň ýa-da süýräň'}
          </Text>
          <Text style={{ color: '#3a4f6e', fontSize: '12px' }}>
            PDF · DOCX · TXT &nbsp;·&nbsp; Iň köp {MAX_FILE_SIZE_MB} MB
          </Text>
        </div>
      </Upload>
    </Card>
  );
}

// ─── Text Input Panel ─────────────────────────────────────────────────────────

function TextInputPanel({ originalText, setOriginalText, suspectText, setSuspectText }) {
  const panelStyle = {
    background: '#0d1626',
    border: '1px solid #1e2d45',
    borderRadius: '12px',
    overflow: 'hidden',
  };

  const labelStyle = {
    color: '#94a3b8',
    fontSize: '11px',
    textTransform: 'uppercase',
    letterSpacing: '1px',
    fontWeight: 700,
  };

  const dotStyle = (color) => ({
    width: 8,
    height: 8,
    borderRadius: '50%',
    background: color,
    display: 'inline-block',
    flexShrink: 0,
  });

  return (
    <Row gutter={[20, 20]}>
      <Col xs={24} lg={12}>
        <Card
          size="small"
          title={
            <Space size={8}>
              <span style={dotStyle('#22c55e')} />
              <Text style={labelStyle}>Asyl Tekst</Text>
            </Space>
          }
          styles={{
            body: { padding: '12px' },
            header: { borderBottom: '1px solid #1e2d45', minHeight: '44px' },
          }}
          style={panelStyle}
        >
          <TextArea
            value={originalText}
            onChange={(e) => setOriginalText(e.target.value)}
            placeholder="Asyl tekstiňizi şu ýere ýazyň..."
            rows={10}
            showCount
            maxLength={5000}
            style={{ fontSize: '14px', resize: 'none' }}
          />
        </Card>
      </Col>

      <Col xs={24} lg={12}>
        <Card
          size="small"
          title={
            <Space size={8}>
              <span style={dotStyle('#f59e0b')} />
              <Text style={labelStyle}>Barlanýan Tekst</Text>
            </Space>
          }
          styles={{
            body: { padding: '12px' },
            header: { borderBottom: '1px solid #1e2d45', minHeight: '44px' },
          }}
          style={panelStyle}
        >
          <TextArea
            value={suspectText}
            onChange={(e) => setSuspectText(e.target.value)}
            placeholder="Barlanýan tekstiňizi şu ýere ýazyň..."
            rows={10}
            showCount
            maxLength={5000}
            style={{ fontSize: '14px', resize: 'none' }}
          />
        </Card>
      </Col>
    </Row>
  );
}

// ─── File Upload Panel ────────────────────────────────────────────────────────

function FileInputPanel({ originalFile, setOriginalFile, suspectFile, setSuspectFile }) {
  return (
    <Row gutter={[20, 20]}>
      <Col xs={24} lg={12}>
        <UploadArea
          label="Asyl Faýl"
          accentColor="#22c55e"
          file={originalFile}
          onSet={setOriginalFile}
        />
      </Col>
      <Col xs={24} lg={12}>
        <UploadArea
          label="Barlanýan Faýl"
          accentColor="#f59e0b"
          file={suspectFile}
          onSet={setSuspectFile}
        />
      </Col>
    </Row>
  );
}

// ─── Loading Panel ────────────────────────────────────────────────────────────

function LoadingPanel({ taskId }) {
  return (
    <Card
      style={{
        borderRadius: '12px',
        background: '#0d1626',
        border: '1px solid #1e2d45',
        textAlign: 'center',
      }}
      styles={{ body: { padding: '40px 24px' } }}
    >
      <Space direction="vertical" size={20} style={{ width: '100%' }}>
        <Spin size="large" />
        <div>
          <Text
            strong
            style={{ fontSize: '16px', color: '#e2e8f0', display: 'block', marginBottom: '4px' }}
          >
            Resminamalar seljerilyär...
          </Text>
          <Text style={{ color: '#4f6f94', fontSize: '13px' }}>
            Bu birnäçe minut alyp biler
          </Text>
        </div>
        <Progress
          percent={75}
          status="active"
          strokeColor={{ from: '#4f8ef7', to: '#7c3aed' }}
          showInfo={false}
          strokeWidth={5}
          style={{ maxWidth: '380px', margin: '0 auto' }}
        />
        {taskId && (
          <div
            style={{
              background: '#1a2740',
              border: '1px solid #1e2d45',
              borderRadius: '8px',
              padding: '12px 20px',
              display: 'inline-block',
            }}
          >
            <Text style={{ color: '#4f6f94', fontSize: '11px', display: 'block', marginBottom: '4px', letterSpacing: '0.5px' }}>
              IŞ BELGISI
            </Text>
            <Text code style={{ color: '#4f8ef7', fontSize: '13px' }}>
              {taskId}
            </Text>
          </div>
        )}
        <Space>
          <ClockCircleOutlined style={{ color: '#3a4f6e' }} />
          <Text style={{ color: '#3a4f6e', fontSize: '12px' }}>
            Netijeler awtomatiki usulda peýda bolar
          </Text>
        </Space>
      </Space>
    </Card>
  );
}

// ─── Result Panel ─────────────────────────────────────────────────────────────

function ResultPanel({ result, taskId, resultStatus, onReset }) {
  const isError = resultStatus === 'error';
  const accentColor = isError ? '#ef4444' : '#22c55e';

  return (
    <Card
      style={{
        borderRadius: '12px',
        background: '#0d1626',
        border: `1px solid ${accentColor}40`,
      }}
      styles={{ body: { padding: '28px' } }}
    >
      <Space direction="vertical" size={20} style={{ width: '100%' }}>
        {/* Header row */}
        <Row align="middle" gutter={16} wrap={false}>
          <Col flex="none">
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: '12px',
                background: `${accentColor}15`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {isError
                ? <WarningOutlined style={{ fontSize: '24px', color: '#ef4444' }} />
                : <CheckCircleOutlined style={{ fontSize: '24px', color: '#22c55e' }} />
              }
            </div>
          </Col>
          <Col flex="auto">
            <Text
              strong
              style={{ fontSize: '17px', color: '#e2e8f0', display: 'block', marginBottom: '4px' }}
            >
              {isError ? 'Seljerme Şowsuz Boldy' : 'Seljerme Tamamlandy'}
            </Text>
            <Tag color={isError ? 'error' : 'success'} style={{ fontSize: '10px', letterSpacing: '0.8px', fontWeight: 700 }}>
              {isError ? 'ŞOWSUZ' : 'TAMAMLANDY'}
            </Tag>
          </Col>
          {taskId && (
            <Col flex="none">
              <div style={{ textAlign: 'right' }}>
                <Text
                  style={{
                    color: '#3a4f6e',
                    fontSize: '10px',
                    display: 'block',
                    marginBottom: '4px',
                    letterSpacing: '0.8px',
                    fontWeight: 700,
                  }}
                >
                  IŞ BELGISI
                </Text>
                <Text copyable code style={{ color: '#4f8ef7', fontSize: '12px' }}>
                  {taskId}
                </Text>
              </div>
            </Col>
          )}
        </Row>

        <Divider style={{ margin: 0, borderColor: '#1e2d45' }} />

        {/* Result content */}
        <div
          style={{
            background: '#0b1120',
            border: '1px solid #1e2d45',
            borderRadius: '10px',
            padding: '20px',
          }}
        >
          <Text
            style={{
              fontSize: '14px',
              lineHeight: '1.9',
              whiteSpace: 'pre-wrap',
              color: '#cbd5e1',
              display: 'block',
            }}
          >
            {result}
          </Text>
        </div>

        <Button
          type="primary"
          icon={<ReloadOutlined />}
          onClick={onReset}
          size="large"
          block
          style={{
            height: '46px',
            borderRadius: '8px',
            background: 'linear-gradient(135deg, #4f8ef7, #7c3aed)',
            border: 'none',
            fontWeight: 600,
            letterSpacing: '0.3px',
          }}
        >
          Täze Barlag
        </Button>
      </Space>
    </Card>
  );
}

// ─── Main App ─────────────────────────────────────────────────────────────────

function AppContent() {
  const [inputType, setInputType] = useState('text');
  const [originalText, setOriginalText] = useState('');
  const [suspectText, setSuspectText] = useState('');
  const [originalFile, setOriginalFile] = useState(null);
  const [suspectFile, setSuspectFile] = useState(null);
  const [result, setResult] = useState('');
  const [resultStatus, setResultStatus] = useState(null); // 'success' | 'error'
  const [loading, setLoading] = useState(false);
  const [taskId, setTaskId] = useState(null);
  const intervalRef = useRef(null);

  // Cleanup interval on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setLoading(false);
  }, []);

  const checkResult = useCallback(
    async (id) => {
      try {
        const response = await axios.get(`${API_URL}/result/${id}`);
        if (response.data.status === 'completed') {
          setResult(response.data.message);
          setResultStatus('success');
          stopPolling();
          return true;
        } else if (response.data.status === 'processing') {
          return false;
        } else {
          setResult(response.data.message || 'Netije tapylmady.');
          setResultStatus('error');
          stopPolling();
          return true;
        }
      } catch {
        setResult('Netijeleri almak başartmady. Gaýtadan synanyşyň.');
        setResultStatus('error');
        stopPolling();
        return true;
      }
    },
    [stopPolling]
  );

  const pollResults = useCallback(
    (id) => {
      let attempts = 0;
      intervalRef.current = setInterval(async () => {
        attempts++;
        const done = await checkResult(id);
        if (done || attempts >= MAX_POLL_ATTEMPTS) {
          stopPolling();
          if (!done) {
            setResult(`Wagt möhleti doldy. Bu iş belgisin saklap, soňra barlaň: ${id}`);
            setResultStatus('error');
          }
        }
      }, POLL_INTERVAL_MS);
    },
    [checkResult, stopPolling]
  );

  const handleSubmit = async () => {
    setLoading(true);
    setResult('');
    setResultStatus(null);
    setTaskId(null);

    const formData = new FormData();
    if (inputType === 'text') {
      formData.append('original_text', originalText);
      formData.append('suspect_text', suspectText);
    } else {
      formData.append('original_file', originalFile);
      formData.append('suspect_file', suspectFile);
    }

    try {
      const response = await axios.post(`${API_URL}/plagiarism-check/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const newTaskId = response.data.task_id;
      setTaskId(newTaskId);
      pollResults(newTaskId);
    } catch (error) {
      if (error.response) {
        setResult(
          `Error ${error.response.status}: ${error.response.data?.detail || JSON.stringify(error.response.data)}`
        );
      } else if (error.request) {
        setResult('Serwer bilen baglanyşyk ýok. Serweriň işleýändigini barlaň.');
      } else {
        setResult(`Näsazlyk: ${error.message}`);
      }
      setResultStatus('error');
      setLoading(false);
    }
  };

  const handleReset = () => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    setResult('');
    setResultStatus(null);
    setTaskId(null);
    setLoading(false);
    setOriginalText('');
    setSuspectText('');
    setOriginalFile(null);
    setSuspectFile(null);
  };

  const canSubmit =
    (inputType === 'text' && originalText.trim() && suspectText.trim()) ||
    (inputType === 'file' && originalFile && suspectFile);

  return (
    <Layout style={{ minHeight: '100vh', background: '#08101e' }}>
      <AppHeader />
      <Content style={{ padding: '40px 16px 60px' }}>
        <div style={{ maxWidth: '960px', margin: '0 auto' }}>
          {/* Hero */}
          <div style={{ textAlign: 'center', marginBottom: '40px' }}>
            <div
              style={{
                width: 64,
                height: 64,
                borderRadius: '16px',
                background: 'linear-gradient(135deg, #4f8ef720, #7c3aed20)',
                border: '1px solid #4f8ef730',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 20px',
              }}
            >
              <SafetyOutlined style={{ fontSize: '28px', color: '#4f8ef7' }} />
            </div>
            <Title level={2} style={{ color: '#e2e8f0', marginBottom: '8px' }}>
              Plagiat Barlagy
            </Title>
            <Text style={{ color: '#4f6f94', fontSize: '15px' }}>
              Iki resminamany deňeşdiriň we göçürilen mazmuny takyk kesgitläň.
            </Text>
          </div>

          {/* Main card */}
          <Card
            style={{
              borderRadius: '16px',
              background: '#111827',
              border: '1px solid #1e2d45',
              boxShadow: '0 24px 64px rgba(0,0,0,0.5)',
            }}
            styles={{ body: { padding: '28px' } }}
          >
            <Space direction="vertical" size={24} style={{ width: '100%' }}>
              {/* Mode toggle */}
              <div style={{ display: 'flex', justifyContent: 'center' }}>
                <Segmented
                  size="large"
                  value={inputType}
                  onChange={setInputType}
                  disabled={loading}
                  options={[
                    {
                      label: (
                        <Space>
                          <FileTextOutlined />
                          Tekst Ýaz
                        </Space>
                      ),
                      value: 'text',
                    },
                    {
                      label: (
                        <Space>
                          <UploadOutlined />
                          Faýl Ýükle
                        </Space>
                      ),
                      value: 'file',
                    },
                  ]}
                />
              </div>

              <Divider style={{ margin: 0, borderColor: '#1e2d45' }} />

              {/* Input panels */}
              {inputType === 'text' ? (
                <TextInputPanel
                  originalText={originalText}
                  setOriginalText={setOriginalText}
                  suspectText={suspectText}
                  setSuspectText={setSuspectText}
                />
              ) : (
                <FileInputPanel
                  originalFile={originalFile}
                  setOriginalFile={setOriginalFile}
                  suspectFile={suspectFile}
                  setSuspectFile={setSuspectFile}
                />
              )}

              {/* Submit button */}
              {!result && (
                <Button
                  type="primary"
                  size="large"
                  icon={loading ? null : <SafetyOutlined />}
                  onClick={handleSubmit}
                  loading={loading}
                  disabled={!canSubmit || loading}
                  block
                  style={{
                    height: '52px',
                    fontSize: '16px',
                    borderRadius: '10px',
                    background:
                      canSubmit && !loading
                        ? 'linear-gradient(135deg, #4f8ef7, #7c3aed)'
                        : undefined,
                    border: 'none',
                    fontWeight: 600,
                    letterSpacing: '0.4px',
                  }}
                >
                  {loading ? 'Seljerilyär...' : 'Plagiat Barlagyny Başlaň'}
                </Button>
              )}

              {/* Loading state */}
              {loading && <LoadingPanel taskId={taskId} />}

              {/* Result */}
              {result && !loading && (
                <ResultPanel
                  result={result}
                  taskId={taskId}
                  resultStatus={resultStatus}
                  onReset={handleReset}
                />
              )}
            </Space>
          </Card>

          {/* Footer */}
          <div style={{ textAlign: 'center', marginTop: '28px' }}>
            <Text style={{ color: '#1e2d45', fontSize: '12px' }}>
              CopyDetect · Plagiat Barlagy Ulgamy
            </Text>
          </div>
        </div>
      </Content>
    </Layout>
  );
}

export default function App() {
  return (
    <ConfigProvider
      theme={{
        algorithm: antTheme.darkAlgorithm,
        token: {
          colorPrimary: '#4f8ef7',
          colorBgContainer: '#111827',
          colorBgElevated: '#1a2535',
          borderRadius: 8,
          fontFamily:
            '-apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", sans-serif',
        },
        components: {
          Segmented: {
            itemSelectedBg: '#1d3a6e',
            itemSelectedColor: '#4f8ef7',
          },
          Card: {
            colorBorderSecondary: '#1e2d45',
          },
        },
      }}
    >
      <AntApp>
        <AppContent />
      </AntApp>
    </ConfigProvider>
  );
}
