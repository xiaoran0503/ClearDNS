package ipgeo

import (
	"net"
	"testing"
)

func TestFormatRegion(t *testing.T) {
	cases := []struct {
		in, want string
	}{
		{"中国|北京|北京|百度|CN", "北京 百度"},
		{"中国|广东省|深圳市|电信|CN", "深圳 电信"},
		{"中国|北京市|0|百度|CN", "北京 百度"},
		{"中国|0|0|阿里云|CN", "中国 阿里云"},
		{"United States|0|0|Cloudflare|US", "美国 Cloudflare"},
		{"United States|California|San Francisco|Google|US", "美国 Google"},
		{"Japan|0|0|0|JP", "日本"},
		{"Hong Kong|0|0|Cloudflare|HK", "香港 Cloudflare"},
		{"内网IP|0|0|0|", ""},
		{"0|0|0|0|0", ""},
		{"", ""},
	}
	for _, tc := range cases {
		if got := formatRegion(tc.in); got != tc.want {
			t.Errorf("formatRegion(%q) = %q, want %q", tc.in, got, tc.want)
		}
	}
}

func TestSkipIP(t *testing.T) {
	mustSkip := []string{"127.0.0.1", "192.168.1.1", "10.0.0.1", "172.16.0.5", "100.64.1.1", "::1", "fc00::1", "169.254.1.1"}
	mustKeep := []string{"110.242.70.57", "1.1.1.1", "2001:4860:4860::8888"}
	for _, s := range mustSkip {
		ip := net.ParseIP(s)
		if ip == nil || !skipIP(ip) {
			t.Errorf("skipIP(%s) = false, want true", s)
		}
	}
	for _, s := range mustKeep {
		ip := net.ParseIP(s)
		if ip == nil || skipIP(ip) {
			t.Errorf("skipIP(%s) = true, want false", s)
		}
	}
}
