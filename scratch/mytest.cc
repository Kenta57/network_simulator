/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * Copyright (c) 2013 ResiliNets, ITTC, University of Kansas
 * Copyright (c) 2019 Yu Nakayama, Ryoma Yasunaga
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation;
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 * Authors: Justin P. Rohrer, Truc Anh N. Nguyen <annguyen@ittc.ku.edu>, Siddharth Gangadhar <siddharth@ittc.ku.edu>
 *
 * James P.G. Sterbenz <jpgs@ittc.ku.edu>, director
 * ResiliNets Research Group  http://wiki.ittc.ku.edu/resilinets
 * Information and Telecommunication Technology Center (ITTC)
 * and Department of Electrical Engineering and Computer Science
 * The University of Kansas Lawrence, KS USA.
 *
 * Work supported in part by NSF FIND (Future Internet Design) Program
 * under grant CNS-0626918 (Postmodern Internet Architecture),
 * NSF grant CNS-1050226 (Multilayer Network Resilience Analysis and Experimentation on GENI),
 * US Department of Defense (DoD), and ITTC at The University of Kansas.
 *
 * “TCP Westwood(+) Protocol Implementation in ns-3”
 * Siddharth Gangadhar, Trúc Anh Ngọc Nguyễn , Greeshma Umapathi, and James P.G. Sterbenz,
 * ICST SIMUTools Workshop on ns-3 (WNS3), Cannes, France, March 2013
 */

#include <iostream>
#include <fstream>
#include <string>

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/error-model.h"
#include "ns3/tcp-header.h"
#include "ns3/udp-header.h"
#include "ns3/enum.h"
#include "ns3/event-id.h"
#include "ns3/flow-monitor-helper.h"
#include "ns3/ipv4-global-routing-helper.h"
#include "ns3/traffic-control-module.h"

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("TcpVariantsComparison");

bool firstCwnd = true;
bool firstSshThr = true;
bool firstRtt = true;
bool firstRto = true;
Ptr<OutputStreamWrapper> cWndStream;
Ptr<OutputStreamWrapper> ssThreshStream;
Ptr<OutputStreamWrapper> rttStream;
Ptr<OutputStreamWrapper> rtoStream;
Ptr<OutputStreamWrapper> nextTxStream;
Ptr<OutputStreamWrapper> nextRxStream;
Ptr<OutputStreamWrapper> inFlightStream;
Ptr<OutputStreamWrapper> ackStream;
Ptr<OutputStreamWrapper> congStateStream;
uint32_t cWndValue;
uint32_t ssThreshValue;
double TH_INTERVAL = 5.0;

// トレース用コールバック関数の設定 関数の引数は決まっている
static void
CwndTracer (Ptr<OutputStreamWrapper> stream, uint32_t oldval, uint32_t newval)
{
  // 観測初め　streamに情報を追加していく
  if (firstCwnd)
    {
      *stream->GetStream () << "0.0 " << oldval << std::endl;
      firstCwnd = false;
    }
  *stream->GetStream () << Simulator::Now ().GetSeconds () << " " << newval << std::endl;
}

static void
SsThreshTracer (Ptr<OutputStreamWrapper> stream, uint32_t oldval, uint32_t newval)
{
  if (firstSshThr)
    {
      *stream->GetStream () << "0.0 " << oldval << std::endl;
      firstSshThr = false;
    }
  *stream->GetStream () << Simulator::Now ().GetSeconds () << " " << newval << std::endl;
}

static void
RttTracer (Ptr<OutputStreamWrapper> stream, Time oldval, Time newval)
{
  if (firstRtt)
    {
      *stream->GetStream () << "0.0 " << oldval.GetSeconds () << std::endl;
      firstRtt = false;
    }
  *stream->GetStream () << Simulator::Now ().GetSeconds () << " " << newval.GetSeconds () << std::endl;
}

static void
RtoTracer (Ptr<OutputStreamWrapper> stream, Time oldval, Time newval)
{
  if (firstRto)
    {
      *stream->GetStream () << "0.0 " << oldval.GetSeconds () << std::endl;
      firstRto = false;
    }
  *stream->GetStream () << Simulator::Now ().GetSeconds () << " " << newval.GetSeconds () << std::endl;
}

static void
NextTxTracer (Ptr<OutputStreamWrapper> stream, SequenceNumber32 old, SequenceNumber32 nextTx)
{
  *stream->GetStream () << Simulator::Now ().GetSeconds () << " " << nextTx << std::endl;
}

static void
InFlightTracer (Ptr<OutputStreamWrapper> stream, uint32_t old, uint32_t inFlight)
{
  *stream->GetStream () << Simulator::Now ().GetSeconds () << " " << inFlight << std::endl;
}

static void
NextRxTracer (Ptr<OutputStreamWrapper> stream, SequenceNumber32 old, SequenceNumber32 nextRx)
{
  *stream->GetStream () << Simulator::Now ().GetSeconds () << " " << nextRx << std::endl;
}

static void
AckTracer (Ptr<OutputStreamWrapper> stream, SequenceNumber32 old, SequenceNumber32 newAck)
{
  *stream->GetStream () << Simulator::Now ().GetSeconds () << " " << newAck << std::endl;
}

static void
CongStateTracer (Ptr<OutputStreamWrapper> stream, TcpSocketState::TcpCongState_t old, TcpSocketState::TcpCongState_t newState)
{
  *stream->GetStream () << Simulator::Now ().GetSeconds () << " " << newState << std::endl;
}

// コールバック関数をトレース対象と紐付ける関数
static void
TraceCwnd (uint32_t nodeId, std::string cwnd_tr_file_name)
{
  // asciiトレースファイルに書き込んでくれるhelper関数
  AsciiTraceHelper ascii;
  // cWndStreamはあらかじめ定義しておく(Ptr<OutputStreamWrapper>)
  Ptr<OutputStreamWrapper> stream = ascii.CreateFileStream (cwnd_tr_file_name.c_str ());
  // CongestionWindowの場所(configパス) "/NodeList/[i]/$ns3::TcpL4Protocol/SocketList/[j]" iがノード番号, jがネットワークデバイス番号
  std::string nodelist = "/NodeList/" + std::to_string(nodeId) + "/$ns3::TcpL4Protocol/SocketList/0/CongestionWindow";
  Config::ConnectWithoutContext (nodelist, MakeBoundCallback (&CwndTracer, stream));
}

static void
TraceSsThresh (uint32_t nodeId, std::string ssthresh_tr_file_name)
{
  AsciiTraceHelper ascii;
  Ptr<OutputStreamWrapper> stream = ascii.CreateFileStream (ssthresh_tr_file_name.c_str ());
  std::string nodelist = "/NodeList/" + std::to_string(nodeId) + "/$ns3::TcpL4Protocol/SocketList/0/SlowStartThreshold";
  Config::ConnectWithoutContext (nodelist, MakeBoundCallback (&SsThreshTracer, stream));
}

static void
TraceRtt (uint32_t nodeId, std::string rtt_tr_file_name)
{
  AsciiTraceHelper ascii;
  Ptr<OutputStreamWrapper> stream = ascii.CreateFileStream (rtt_tr_file_name.c_str ());
  std::string nodelist = "/NodeList/" + std::to_string(nodeId) + "/$ns3::TcpL4Protocol/SocketList/0/RTT";
  Config::ConnectWithoutContext (nodelist, MakeBoundCallback (&RttTracer, stream));
}

static void
TraceRto (uint32_t nodeId, std::string rto_tr_file_name)
{
  AsciiTraceHelper ascii;
  Ptr<OutputStreamWrapper> stream = ascii.CreateFileStream (rto_tr_file_name.c_str ());
  std::string nodelist = "/NodeList/" + std::to_string(nodeId) + "/$ns3::TcpL4Protocol/SocketList/0/RTO";
  Config::ConnectWithoutContext (nodelist, MakeBoundCallback (&RtoTracer, stream));
}

static void
TraceNextTx (uint32_t nodeId, std::string &next_tx_seq_file_name)
{
  AsciiTraceHelper ascii;
  Ptr<OutputStreamWrapper> stream = ascii.CreateFileStream (next_tx_seq_file_name.c_str ());
  std::string nodelist = "/NodeList/" + std::to_string(nodeId) + "/$ns3::TcpL4Protocol/SocketList/0/NextTxSequence";
  Config::ConnectWithoutContext (nodelist, MakeBoundCallback (&NextTxTracer, stream));
}

static void
TraceInFlight (uint32_t nodeId, std::string &in_flight_file_name)
{
  AsciiTraceHelper ascii;
  Ptr<OutputStreamWrapper> stream = ascii.CreateFileStream (in_flight_file_name.c_str ());
  std::string nodelist = "/NodeList/" + std::to_string(nodeId) + "/$ns3::TcpL4Protocol/SocketList/0/BytesInFlight";
  Config::ConnectWithoutContext (nodelist, MakeBoundCallback (&InFlightTracer, stream));
}

static void
TraceNextRx (uint32_t nodeId, std::string &next_rx_seq_file_name)
{
  AsciiTraceHelper ascii;
  Ptr<OutputStreamWrapper> stream = ascii.CreateFileStream (next_rx_seq_file_name.c_str ());
  std::string nodelist = "/NodeList/" + std::to_string(nodeId) + "/$ns3::TcpL4Protocol/SocketList/1/RxBuffer/NextRxSequence";
  Config::ConnectWithoutContext (nodelist, MakeBoundCallback (&NextRxTracer, stream));
}

static void
TraceAck (uint32_t nodeId, std::string &ack_file_name)
{
  AsciiTraceHelper ascii;
  Ptr<OutputStreamWrapper> stream = ascii.CreateFileStream (ack_file_name.c_str ());
  std::string nodelist = "/NodeList/" + std::to_string(nodeId) + "/$ns3::TcpL4Protocol/SocketList/0/HighestRxAck";
  Config::ConnectWithoutContext (nodelist, MakeBoundCallback (&AckTracer, stream));
}

static void
TraceCongState (uint32_t nodeId, std::string &cong_state_file_name)
{
  AsciiTraceHelper ascii;
  Ptr<OutputStreamWrapper> stream = ascii.CreateFileStream (cong_state_file_name.c_str ());
  std::string nodelist = "/NodeList/" + std::to_string(nodeId) + "/$ns3::TcpL4Protocol/SocketList/0/CongState";
  Config::ConnectWithoutContext (nodelist, MakeBoundCallback (&CongStateTracer, stream));
}

static std::string
GetTcpAlgorithm (std::string transport_prot)
{
	std::string alg;
	if (transport_prot.compare ("TcpNewReno") == 0) {
		alg = "ns3::TcpNewReno";
	} else if (transport_prot.compare ("TcpHybla") == 0) {
		alg = "ns3::TcpHybla";
	} else if (transport_prot.compare ("TcpHighSpeed") == 0) {
		alg = "ns3::TcpHighSpeed";
	} else if (transport_prot.compare ("TcpVegas") == 0) {
		alg = "ns3::TcpVegas";
	} else if (transport_prot.compare ("TcpScalable") == 0) {
		alg = "ns3::TcpScalable";
	} else if (transport_prot.compare ("TcpHtcp") == 0) {
		alg = "ns3::TcpHtcp";
	} else if (transport_prot.compare ("TcpVeno") == 0) {
		alg = "ns3::TcpVeno";
	} else if (transport_prot.compare ("TcpBic") == 0) {
		alg = "ns3::TcpBic";
	} else if (transport_prot.compare ("TcpCubic") == 0) {
		alg = "ns3::TcpCubic";
	} else if (transport_prot.compare ("TcpBbr") == 0) {
		alg = "ns3::TcpBbr";
	} else {
		NS_LOG_DEBUG ("Invalid TCP version");
		exit (1);
	}
	return alg;
}

static void
SetTcpAlgorithm2Node (uint32_t nodeId, std::string transport_prot)
{
  // configパス ns3のcoreファイルに書かれている情報の場所を表す？ 今回の場合だとsocketのタイプが格納してある場所
	std::string nodelist = "/NodeList/" + std::to_string(nodeId) + "/$ns3::TcpL4Protocol/SocketType";
  // 名前からtype idを呼ぶ
	TypeId tid = TypeId::LookupByName(GetTcpAlgorithm(transport_prot));
  // デフォルトではcubicになっているのでそれをtransport_protに変更
	Config::Set(nodelist, TypeIdValue(tid));
}

static void // trace throughput in Mbps
TraceThroughput (Ptr<Application> app, Ptr<OutputStreamWrapper> stream, uint32_t oldTotalBytes)
{
  // PacketSinkにcast
	Ptr <PacketSink> pktSink = DynamicCast <PacketSink> (app);
  // sink appが今まで受け取ったtotalのbyte数
	uint32_t newTotalBytes = pktSink->GetTotalRx ();
  // byte -> Mbit 
	*stream->GetStream() << Simulator::Now ().GetSeconds () << "\t" << (newTotalBytes - oldTotalBytes)*8.0/TH_INTERVAL/1000/1000 << std::endl;
  // totalを再帰的に渡すことで差分を取ることできる
	Simulator::Schedule (Seconds (TH_INTERVAL), &TraceThroughput, app, stream, newTotalBytes);
}

static void
StartAppTrace(ApplicationContainer sinkapp, std::string th_file_name)
{
  // asciiトレースファイルに書き込んでくれるhelper関数
	AsciiTraceHelper ascii;
	Ptr<OutputStreamWrapper> st1 = ascii.CreateFileStream(th_file_name);
  // TraceThroughput関数の最初の呼び出し oldTotalBytesを0にしておく
	Simulator::Schedule (Seconds (TH_INTERVAL), &TraceThroughput, sinkapp.Get(0), st1, 0);
}

static void
TraceQueue (Ptr< Queue< Packet > > queue, Ptr<OutputStreamWrapper> stream, std::string type)
{
  // queueにある*数
	uint32_t sizeB = queue->GetNBytes ();
	uint32_t sizeP = queue->GetNPackets ();
  // 受信した*数
	uint32_t  recB = queue->GetTotalReceivedBytes ();
	uint32_t  recP = queue->GetTotalReceivedPackets ();
  // dropした*数
	uint32_t dropB = queue->GetTotalDroppedBytes ();
	uint32_t dropP = queue->GetTotalDroppedPackets ();

  // typeに応じて単位をbyteかpacketにしたものを書き込む
	if(type.compare("bytes") == 0) {
		*stream->GetStream() << Simulator::Now ().GetSeconds () << "\t" << sizeB << "\t" << recB << "\t" << dropB << std::endl;
	} else {
		*stream->GetStream() << Simulator::Now ().GetSeconds () << "\t" << sizeP << "\t" << recP << "\t" << dropP << std::endl;
	}
  // 再帰的に呼び出す
	Simulator::Schedule (Seconds (TH_INTERVAL), &TraceQueue, queue, stream, type);
}

static void
StartQueueTrace (Ptr<NetDevice> dev, std::string type, std::string q_file_name)
{
  // cast
	Ptr<PointToPointNetDevice> nd = StaticCast<PointToPointNetDevice> (dev);
  // netdeviceのqueueを取り出す
	Ptr< Queue< Packet > > queue = nd->GetQueue ();

  // asciiデータのためのhelper関数
	AsciiTraceHelper ascii;
	Ptr<OutputStreamWrapper> st1 = ascii.CreateFileStream(q_file_name);

	*st1->GetStream() << "Time\t" << "size\t" << "received\t" << "dropped" << "\n";
	Simulator::Schedule (Seconds (TH_INTERVAL), &TraceQueue, queue, st1, type);
}

static PointToPointHelper
GetP2PLink (std::string bandwidth, std::string delay, uint32_t q_size)
{
	PointToPointHelper p2p;
	p2p.SetDeviceAttribute ("DataRate", StringValue (bandwidth));
	p2p.SetChannelAttribute ("Delay", StringValue (delay));
	// p2p.SetQueue ("ns3::DropTailQueue", "MaxPackets", UintegerValue (q_size));
	p2p.SetQueue ("ns3::DropTailQueue", "MaxSize", StringValue (std::to_string(q_size)+'p'));
	return p2p;
}

int main (int argc, char *argv[])
{
  std::string transport_prot = "TcpCubic";
  double error_p_local = 0.0;
  double error_p_global = 0.0;
  std::string bandwidth = "1Mbps";
  std::string delay = "1ms";
  std::string access_bandwidth = "100Mbps";
  std::string access_delay = "10ms";
  bool tracing = false;
  std::string prefix_file_name = "TcpDelayBase";
  double data_mbytes = 0;
  uint32_t mtu_bytes = 1500;
  uint16_t num_flows = 1;
  float duration = 100;
  uint32_t run = 0;
  uint32_t q_size = 10;
  bool flow_monitor = false;
  bool pcap = false;


  CommandLine cmd;
  cmd.AddValue ("transport_prot", "Transport protocol to use: TcpNewReno, "
                "TcpHybla, TcpHighSpeed, TcpHtcp, TcpVegas, TcpScalable, TcpVeno, "
                "TcpBic, TcpCubic, TcpBbr, TcpYeah, TcpIllinois, TcpWestwood, TcpWestwoodPlus ", transport_prot);
  cmd.AddValue ("error_p_local", "Packet error rate", error_p_local);
  cmd.AddValue ("error_p_global", "Packet error rate", error_p_global);
  cmd.AddValue ("bandwidth", "Bottleneck bandwidth", bandwidth);
  cmd.AddValue ("delay", "Bottleneck delay", delay);
  cmd.AddValue ("access_bandwidth", "Access link bandwidth", access_bandwidth);
  cmd.AddValue ("access_delay", "Access link delay", access_delay);
  cmd.AddValue ("tracing", "Flag to enable/disable tracing", tracing);
  cmd.AddValue ("prefix_name", "Prefix of output trace file", prefix_file_name);
  cmd.AddValue ("data", "Number of Megabytes of data to transmit", data_mbytes);
  cmd.AddValue ("mtu", "Size of IP packets to send in bytes", mtu_bytes);
  cmd.AddValue ("num_flows", "Number of flows", num_flows);
  cmd.AddValue ("duration", "Time to allow flows to run in seconds", duration);
  cmd.AddValue ("run", "Run index (for setting repeatable seeds)", run);
  cmd.AddValue ("q_size", "Queue size", q_size);
  cmd.AddValue ("flow_monitor", "Enable flow monitor", flow_monitor);
  cmd.AddValue ("pcap_tracing", "Enable or disable PCAP tracing", pcap);
  cmd.Parse (argc, argv);

  SeedManager::SetSeed (1);
  SeedManager::SetRun (run);

  // User may find it convenient to enable logging
  //LogComponentEnable("TcpVariantsComparison", LOG_LEVEL_ALL);
  //LogComponentEnable("BulkSendApplication", LOG_LEVEL_INFO);
  //LogComponentEnable("PfifoFastQueueDisc", LOG_LEVEL_ALL);

  // Calculate the ADU size
  Header* temp_header = new Ipv4Header ();
  uint32_t ip_header = temp_header->GetSerializedSize ();
  NS_LOG_LOGIC ("IP Header size is: " << ip_header);
  delete temp_header;
  temp_header = new TcpHeader ();
  uint32_t tcp_header = temp_header->GetSerializedSize ();
  NS_LOG_LOGIC ("TCP Header size is: " << tcp_header);
  delete temp_header;
  uint32_t tcp_adu_size = mtu_bytes - 20 - (ip_header + tcp_header);
  NS_LOG_LOGIC ("TCP ADU size is: " << tcp_adu_size);

  // Set the simulation start and stop time
  float start_time = 0.1;
  float stop_time = start_time + duration;

  // 4 MB of TCP buffer
  Config::SetDefault ("ns3::TcpSocket::RcvBufSize", UintegerValue (1 << 21));
  Config::SetDefault ("ns3::TcpSocket::SndBufSize", UintegerValue (1 << 21));

  //Config::SetDefault ("ns3::TcpSocketBase::MaxWindowSize", UintegerValue (65535));
  //Config::SetDefault ("ns3::TcpSocketBase::WindowScaling", BooleanValue (false));

  // Create gateways, sources, and sinks
  NodeContainer gateways;
  gateways.Create (2);
  NodeContainer sources;
  sources.Create (num_flows);
  NodeContainer sinks;
  sinks.Create (num_flows);

  // Configure the error model
  // Here we use RateErrorModel with packet error rate

  // <>について
  // テンプレート関数<>の中に明示的に型を入れて使う
  // 下のように関数を定義することで動的に関数の返り値を変更できる
  // template <class Type>
  // Type add(Type a, Type b){
  //   Type result = a + b;
  //   return result;
  // }
  // add<int>(x_i, y_d)みたいに使うことができる

  // Ptrはスマートポインタのようなもの
  // std::auto_ptr<int> ptr(new int(10));
  // のように動的にメモリを確保する

  // 確率分布の種類を定義
  Ptr<UniformRandomVariable> uv = CreateObject<UniformRandomVariable> ();
  // シード値を決定
  uv->SetStream (50);
  RateErrorModel error_model_local;
  // error_model_localに確率分布を設定
  error_model_local.SetRandomVariable (uv);
  // パケットベースのユニットの設定
  error_model_local.SetUnit (RateErrorModel::ERROR_UNIT_PACKET);
  // ロス率を決定
  error_model_local.SetRate (error_p_local);

  RateErrorModel error_model_global;
  // error_model_localに確率分布を設定
  error_model_global.SetRandomVariable (uv);
  // パケットベースのユニットの設定
  error_model_global.SetUnit (RateErrorModel::ERROR_UNIT_PACKET);
  // ロス率を決定
  error_model_global.SetRate (error_p_global);

  // 上でGetP2PLink関数を定義, 引数の通りのようなpointtopointhelperを返す関数(queueはdroptail)
  PointToPointHelper LocalLink = GetP2PLink ("10Mbps", access_delay, q_size);
  PointToPointHelper GwLink = GetP2PLink ("20Mbps", delay, q_size);
  PointToPointHelper UnReLink = GetP2PLink ("10Mbps", delay, q_size);

  // 1本目のフローのエラー率の決定(下流)
  PointToPointHelper LocalInitialLink = GetP2PLink ("10Mbps", access_delay, q_size);
  if(error_p_local > 0){
    LocalInitialLink.SetDeviceAttribute ("ReceiveErrorModel", PointerValue (&error_model_local));
  }

  // 1本目のフローのエラー率の決定(上流)
  PointToPointHelper UnReInitialLink = GetP2PLink ("10Mbps", delay, q_size);
  if(error_p_global > 0){
    UnReInitialLink.SetDeviceAttribute ("ReceiveErrorModel", PointerValue (&error_model_global));
  }

  // GwLink.SetDeviceAttribute ("ReceiveErrorModel", PointerValue (&error_model));

  // プロトコルスタックの決定
  InternetStackHelper stack;
  stack.InstallAll ();

  // IPアドレス割り当ての準備
  Ipv4AddressHelper address;
  address.SetBase ("10.0.0.0", "255.255.255.0");

  // 
  Ipv4InterfaceContainer sink_interfaces;

  for (int i = 0; i < num_flows; i++)
    {
      int q = 0;
      // ネットデバイス(インターフェース)の設定
      NetDeviceContainer devices;
      // LocalLinkの設定のリンクをsourcesのi番目とgatewaysの0番目のノードに張る
      if(i==0){
        devices = LocalInitialLink.Install (sources.Get (i), gateways.Get (0));
      }else{
        devices = LocalLink.Install (sources.Get (i), gateways.Get (0));
      }
      // addressで設定したネットワーク番号をインクリメントして新しいネットワークの割り当て用のIpv4AddressHelperを作るイメージ
      address.NewNetwork ();
      // ipアドレスの割り当て
      Ipv4InterfaceContainer interfaces = address.Assign (devices);

      // 中間部のトポロジーの作成
      if(i == 0) {
        devices = GwLink.Install (gateways.Get (0), gateways.Get (1));
        address.NewNetwork ();
        interfaces = address.Assign (devices);
        StartQueueTrace(devices.Get(0), "packets", prefix_file_name + "-queue-" + std::to_string(q++) + ".data");
      }

      if(i==0){
        devices = UnReInitialLink.Install (gateways.Get (1), sinks.Get (i));
      }else{
        devices = UnReLink.Install (gateways.Get (1), sinks.Get (i));
      }

      address.NewNetwork ();
      interfaces = address.Assign (devices);
      StartQueueTrace(devices.Get(0), "packets", prefix_file_name + "-queue-" + std::to_string(q++) + ".data");

      // .Get(i)はPtr<Ipv4>とそれを保存するindexのstd::pairを返す, ipが振られたnetwork deviceを集めたコンテナ
      sink_interfaces.Add (interfaces.Get (1));

    }

  NS_LOG_INFO ("Initialize Global Routing.");
  Ipv4GlobalRoutingHelper::PopulateRoutingTables ();


  for (uint16_t i = 0; i < sources.GetN (); i++)
    {
      uint16_t port = 50000 + i;
      // アドレスの設定 GetAnyは0.0.0.0を表す
      Address sinkLocalAddress (InetSocketAddress (Ipv4Address::GetAny (), port));
      // TCPの受信端(sink)はPacketSinkHelperで作る. 
      PacketSinkHelper sinkHelper ("ns3::TcpSocketFactory", sinkLocalAddress);
      // sinkのipアドレスとポート
      AddressValue remoteAddress (InetSocketAddress (sink_interfaces.GetAddress (i, 0), port));

      // sourcesのi番目のノードのtcpアルゴリズムをtrasport_protに変更
      SetTcpAlgorithm2Node (sources.Get (i)->GetId(), transport_prot);

      Config::SetDefault ("ns3::TcpSocket::SegmentSize", UintegerValue (tcp_adu_size));
      // BulkSendApplicationはできる限り速くデータを送信するトラフィックジェネレータ　インスタンスの用意
      BulkSendHelper ftp ("ns3::TcpSocketFactory", Address ());
      // インスタンスの属性設定
      // 送信先のアドレス　remoteAddressはsinkノードのアドレス
      ftp.SetAttribute ("Remote", remoteAddress);
      // 1回に送信する量(おそらくMSSのこと)
      ftp.SetAttribute ("SendSize", UintegerValue (tcp_adu_size));
      // 送信するデータ量(この値を0にすると無限大を意味する)
      ftp.SetAttribute ("MaxBytes", UintegerValue (int(data_mbytes * 1000000)));

      // i番目のsourceのノードに設定したアプリケーションを置く
      ApplicationContainer sourceApp = ftp.Install (sources.Get (i));
      // アプリケーションの開始, 終了時刻を決定
      sourceApp.Start (Seconds (start_time * i));
      sourceApp.Stop (Seconds (stop_time));

      // TcpSocketFactoryはTCP socketインスタンスを作るためのapi, rx(reception)用のソケットのプロトコルの決定？
      sinkHelper.SetAttribute ("Protocol", TypeIdValue (TcpSocketFactory::GetTypeId ()));
      ApplicationContainer sinkApp = sinkHelper.Install (sinks.Get (i));
      // アプリケーションの開始, 終了時刻を決定
      sinkApp.Start (Seconds (start_time * i));
      sinkApp.Stop (Seconds (stop_time));

      // Throughputのtrace
      StartAppTrace(sinkApp, prefix_file_name + "-flw" + std::to_string(i) + "-throughput.data");
    }

  // Set up tracing if enabled
  if (tracing)
    {
      /*
      std::ofstream ascii;
      Ptr<OutputStreamWrapper> ascii_wrap;
      ascii.open ((prefix_file_name + "-ascii").c_str ());
      ascii_wrap = new OutputStreamWrapper ((prefix_file_name + "-ascii").c_str (),
                                            std::ios::out);
      stack.EnableAsciiIpv4All (ascii_wrap);
      */

      for (int i = 0; i < num_flows; i++) {
        // 0.00001sごとに再帰的に関数が呼び出される 引数は時間, 関数, その関数の引数
        Simulator::Schedule (Seconds (0.00001+start_time * i), &TraceCwnd, sources.Get (i)->GetId(), prefix_file_name + "-flw" + std::to_string(i) + "-cwnd.data");
        Simulator::Schedule (Seconds (0.00001+start_time * i), &TraceSsThresh, sources.Get (i)->GetId(), prefix_file_name + "-flw" + std::to_string(i) + "-ssth.data");
        Simulator::Schedule (Seconds (0.00001+start_time * i), &TraceRtt, sources.Get (i)->GetId(), prefix_file_name + "-flw" + std::to_string(i) + "-rtt.data");
        Simulator::Schedule (Seconds (0.00001+start_time * i), &TraceRto, sources.Get (i)->GetId(), prefix_file_name + "-flw" + std::to_string(i) + "-rto.data");
        Simulator::Schedule (Seconds (0.00001+start_time * i), &TraceNextTx, sources.Get (i)->GetId(), prefix_file_name + "-flw" + std::to_string(i) + "-next-tx.data");
        Simulator::Schedule (Seconds (0.00001+start_time * i), &TraceInFlight, sources.Get (i)->GetId(), prefix_file_name + "-flw" + std::to_string(i) + "-inflight.data");
        Simulator::Schedule (Seconds (0.1+start_time * i), &TraceNextRx, sinks.Get (i)->GetId(),  prefix_file_name + "-flw" + std::to_string(i) + "-next-rx.data");
        Simulator::Schedule (Seconds (0.00001+start_time * i), &TraceAck, sources.Get (i)->GetId(), prefix_file_name + "-flw" + std::to_string(i) + "-ack.data");
        Simulator::Schedule (Seconds (0.00001+start_time * i), &TraceCongState, sources.Get (i)->GetId(), prefix_file_name + "-flw" + std::to_string(i) + "-cong-state.data");
      }
    }

  // pcapの出力
  if (pcap)
    {
      UnReLink.EnablePcapAll (prefix_file_name, true);
      LocalLink.EnablePcapAll (prefix_file_name, true);
    }

  // Flow monitor
  FlowMonitorHelper flowHelper;
  if (flow_monitor)
    {
      flowHelper.InstallAll ();
    }

  Simulator::Stop (Seconds (stop_time));
  Simulator::Run ();

  if (flow_monitor)
    {
      flowHelper.SerializeToXmlFile (prefix_file_name + ".flowmonitor", true, true);
    }

  Simulator::Destroy ();
  return 0;
}
