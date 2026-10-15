package view

// Independent external-collector qualification only. All markers and payloads
// below are synthetic and cannot serve as Nizam hosted execution evidence.
import (
	"bufio"
	"bytes"
	"crypto/sha256"
	"errors"
	"hash"
	"io"
	"strings"
	"testing"
)

const wa123SyntheticMarker = "WA123_SYNTHETIC_MARKER=not-hosted-proof"
const wa123LineBoundary = 16 * 1024 * 1024

func TestWA123CollectorRepairOrdinaryAndEmpty(t *testing.T) {
	const prefix = "synthetic-job\tsynthetic-step\t"
	cases := []struct{ name, input, want string }{
		{"empty-input", "", ""},
		{"empty-line", "\n", prefix + "\n"},
		{"ordinary-and-empty", "alpha\n\nomega\n", prefix + "alpha\n" + prefix + "\n" + prefix + "omega\n"},
		{"unterminated-tail", "tail", prefix + "tail\n"},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			var out bytes.Buffer
			if err := copyLogWithLinePrefix(&out, strings.NewReader(tc.input), prefix); err != nil {
				t.Fatalf("unexpected error: %v", err)
			}
			if got := out.String(); got != tc.want {
				t.Fatalf("output mismatch: got %q, want %q", got, tc.want)
			}
		})
	}
}

func TestWA123CollectorRepairLongLineThenMarker(t *testing.T) {
	const prefix = "synthetic-job\tUNKNOWN STEP\t"
	cases := []struct{ name string; size int }{
		{"above-default-scanner-limit", 65537},
		{"actual-result-line-size-synthetic-bytes", 356060},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			line := strings.Repeat("x", tc.size)
			input := line + "\n" + wa123SyntheticMarker + "\n"
			want := prefix + line + "\n" + prefix + wa123SyntheticMarker + "\n"
			var out bytes.Buffer
			if err := copyLogWithLinePrefix(&out, strings.NewReader(input), prefix); err != nil {
				t.Fatalf("unexpected error for %d-byte line: %v", tc.size, err)
			}
			if !bytes.Equal(out.Bytes(), []byte(want)) {
				t.Fatalf("complete prefixed line and later marker lost: got %d bytes, want %d", out.Len(), len(want))
			}
		})
	}
}

// Stream boundary payloads; avoid allocating multiple 16MiB input/golden copies.
// The repaired scanner and formatter still need their own finite line buffers.
type wa123RepeatReader struct{}

func (wa123RepeatReader) Read(p []byte) (int, error) {
	for i := range p { p[i] = 'x' }
	return len(p), nil
}

type wa123DigestWriter struct {
	h hash.Hash
	count int64
}

func (w *wa123DigestWriter) Write(p []byte) (int, error) {
	n, err := w.h.Write(p)
	w.count += int64(n)
	return n, err
}

func TestWA123CollectorRepairFiniteLineBoundary(t *testing.T) {
	const prefix = "synthetic\t"
	input := io.MultiReader(io.LimitReader(wa123RepeatReader{}, wa123LineBoundary), strings.NewReader("\n" + wa123SyntheticMarker + "\n"))
	out := &wa123DigestWriter{h: sha256.New()}
	if err := copyLogWithLinePrefix(out, input, prefix); err != nil {
		t.Fatalf("16MiB line plus newline must fit the declared capacity: %v", err)
	}
	want := &wa123DigestWriter{h: sha256.New()}
	if _, err := io.WriteString(want, prefix); err != nil { t.Fatal(err) }
	if _, err := io.CopyN(want, wa123RepeatReader{}, wa123LineBoundary); err != nil { t.Fatal(err) }
	if _, err := io.WriteString(want, "\n" + prefix + wa123SyntheticMarker + "\n"); err != nil { t.Fatal(err) }
	if out.count != want.count || !bytes.Equal(out.h.Sum(nil), want.h.Sum(nil)) {
		t.Fatalf("boundary line/tail corruption: got %d bytes, want %d", out.count, want.count)
	}
}

func TestWA123CollectorRepairOverLimitReturnsError(t *testing.T) {
	input := io.MultiReader(io.LimitReader(wa123RepeatReader{}, wa123LineBoundary + 1), strings.NewReader("\n" + wa123SyntheticMarker + "\n"))
	out := &wa123DigestWriter{h: sha256.New()}
	err := copyLogWithLinePrefix(out, input, "synthetic\t")
	if !errors.Is(err, bufio.ErrTooLong) {
		t.Fatalf("oversized line must return scanner failure; got %v", err)
	}
	if out.count != 0 { t.Fatalf("oversized first line must not emit a partial line or later marker; got %d bytes", out.count) }
}

type wa123ReaderError struct {
	payload *strings.Reader
	err error
}

func (r *wa123ReaderError) Read(p []byte) (int, error) {
	if r.payload.Len() != 0 { return r.payload.Read(p) }
	return 0, r.err
}

func TestWA123CollectorRepairReaderError(t *testing.T) {
	failure := errors.New("synthetic read failure")
	input := &wa123ReaderError{payload: strings.NewReader("before\n"), err: failure}
	var out bytes.Buffer
	err := copyLogWithLinePrefix(&out, input, "synthetic\t")
	if !errors.Is(err, failure) { t.Fatalf("reader error was hidden: %v", err) }
	if out.String() != "synthetic\tbefore\n" { t.Fatalf("completed preceding line changed: %q", out.String()) }
}

type wa123WriterError struct{ err error }

func (w wa123WriterError) Write([]byte) (int, error) { return 0, w.err }

func TestWA123CollectorRepairWriterError(t *testing.T) {
	failure := errors.New("synthetic write failure")
	err := copyLogWithLinePrefix(wa123WriterError{err: failure}, strings.NewReader("before\n" + wa123SyntheticMarker + "\n"), "synthetic\t")
	if !errors.Is(err, failure) { t.Fatalf("writer error was hidden: %v", err) }
}
