;;;; Fixed built-ins-only SBCL worker. Private input is data, with reader eval off.
;;;; The control stream is independent of all project output streams.
(defpackage :nizam-session (:use :cl))
(in-package :nizam-session)

(defstruct json-object pairs)
(defun object (&rest pairs) (make-json-object :pairs pairs))
(defun truth (value) (if value :true :false))
(defun utf8-width (char)
  (let ((code (char-code char)))
    (cond ((< code 128) 1) ((< code 2048) 2) ((< code 65536) 3) (t 4))))

;;; A bounded sink prevents a single WRITE-STRING or project printer from
;;; accumulating unbounded output. Strict sinks abort internal JSON rendering;
;;; project sinks discard excess bytes without pretending a scalar succeeded.
(defclass bounded-stream (sb-gray:fundamental-character-output-stream)
  ((buffer :initform (make-array 0 :element-type 'character :adjustable t :fill-pointer 0)
           :accessor buffer)
   (limit :initarg :limit :reader byte-limit)
   (bytes :initform 0 :accessor byte-count)
   (strict :initarg :strict :initform nil :reader strict-p)
   (truncated :initform nil :accessor truncated-p)))
(defmethod sb-gray:stream-write-char ((stream bounded-stream) char)
  (let ((width (utf8-width char)))
    (if (<= (+ (byte-count stream) width) (byte-limit stream))
        (progn (vector-push-extend char (buffer stream)) (incf (byte-count stream) width))
        (progn (setf (truncated-p stream) t)
               (when (strict-p stream) (error "Rendering budget exhausted")))))
  char)
(defmethod sb-gray:stream-write-string ((stream bounded-stream) text &optional (start 0) end)
  (loop for index from start below (or end (length text))
        while (or (strict-p stream) (not (truncated-p stream)))
        do (sb-gray:stream-write-char stream (char text index)))
  text)
(defmethod sb-gray:stream-line-column ((stream bounded-stream)) (declare (ignore stream)) nil)
(defmethod sb-gray:stream-force-output ((stream bounded-stream)) (declare (ignore stream)) nil)
(defmethod sb-gray:stream-finish-output ((stream bounded-stream)) (declare (ignore stream)) nil)

(defun json-string (text stream)
  (write-char #\" stream)
  (loop for char across text do
    (case char
      (#\" (write-string "\\\"" stream))
      (#\\ (write-string "\\\\" stream))
      (#\Newline (write-string "\\n" stream))
      (#\Return (write-string "\\r" stream))
      (#\Tab (write-string "\\t" stream))
      (otherwise (if (< (char-code char) 32)
                     (format stream "\\u~4,'0X" (char-code char))
                     (write-char char stream)))))
  (write-char #\" stream))
(defun json-write (value stream)
  (cond ((eq value :true) (write-string "true" stream))
        ((eq value :false) (write-string "false" stream))
        ((null value) (write-string "null" stream))
        ((stringp value) (json-string value stream))
        ((integerp value) (format stream "~D" value))
        ((typep value 'json-object)
         (write-char #\{ stream)
         (loop for (key item) on (json-object-pairs value) by #'cddr for first = t then nil do
           (unless first (write-char #\, stream))
           (json-string key stream) (write-char #\: stream) (json-write item stream))
         (write-char #\} stream))
        ((and (vectorp value) (not (stringp value)))
         (write-char #\[ stream)
         (loop for item across value for first = t then nil do
           (unless first (write-char #\, stream)) (json-write item stream))
         (write-char #\] stream))
        (t (error "Value has no supported exact JSON scalar representation"))))
(defun json-text (value limit)
  (let ((stream (make-instance 'bounded-stream :limit limit :strict t)))
    (json-write value stream)
    (copy-seq (buffer stream))))
(defun generation-json (generation)
  (object "counter" (getf generation :counter) "nonce" (getf generation :nonce)))

(defvar *wire* (sb-sys:make-fd-stream 3 :output t :element-type 'character
                                     :external-format :utf-8 :buffering :none :auto-close nil))
(defun send-frame (frame)
  (write-string (json-text frame 65535) *wire*)
  (terpri *wire*) (finish-output *wire*))
(defun receive-frame ()
  (let ((*read-eval* nil) (*package* (find-package :keyword))
        (quoted nil) (escaped nil) (bytes 0)
        (text (make-array 0 :element-type 'character :adjustable t :fill-pointer 0)))
    ;; A source string may contain literal newlines. Only an unquoted newline
    ;; terminates the private data frame; escaping cannot enable reader eval.
    (loop for char = (read-char *standard-input* nil nil) do
      (unless char (sb-ext:exit :code 0))
      (incf bytes (utf8-width char))
      (when (> bytes 65536) (error "Oversized private frame"))
      (when (and (char= char #\Newline) (not quoted)) (return))
      (vector-push-extend char text)
      (cond (escaped (setf escaped nil))
            ((and quoted (char= char #\\)) (setf escaped t))
            ((char= char #\") (setf quoted (not quoted)))))
    (multiple-value-bind (value end) (read-from-string text nil nil)
      (unless (and (listp value) (= end (length text))) (error "Malformed private frame"))
      value)))

;;; Trusted names only: no condition-report, restart-report, PRINT-OBJECT,
;;; arguments or arbitrary objects are dispatched while collecting metadata.
;;; Actual rendering paths bind depth6/length32/circleT. Metadata strings are
;;; capped too, including names obtained from project-created symbols.
(defun bounded-name (value &optional (depth 0))
  (cond ((>= depth *print-level*) "...")
        ((symbolp value)
         (let ((name (symbol-name value))) (subseq name 0 (min 256 (length name)))))
        ((stringp value) (subseq value 0 (min 256 (length value))))
        ((consp value)
         (format nil "(~{~A~^ ~})"
                 (loop for item in value for index below *print-length*
                       collect (bounded-name item (1+ depth)))))
        (t "<opaque>")))
(defun minimal-diagnostic (condition failed)
  (object "condition" (object "type" (bounded-name (type-of condition))
                              "text" "Trusted condition identity; project report omitted"
                              "fallback" :true)
          "backtrace" #() "restarts" #() "truncated" :true "capture_failed" (truth failed)))
(defun capture-condition (condition seconds remaining)
  ;; Capture is executed by HANDLER-BIND in the signalling worker, before
  ;; THROW unwinds it. A finite timer covers introspection and all encoding.
  ;; Expiry abandons capture; no unsafe rendering is retried in the fallback.
  (let ((*print-level* 6) (*print-length* 32) (*print-circle* t)
        (*print-pretty* nil) (*print-readably* nil)
        (answer nil))
    (when (and (> seconds 0) (> remaining 1))
      (handler-case
          (sb-ext:with-timeout seconds
            (let ((frames nil) (restarts nil) (index 0))
              ;; Exported SB-DI zero/one-argument API, qualified on actual
              ;; SBCL with an active named frame and restart before unwind.
              (loop for frame = (sb-di:top-frame) then (sb-di:frame-down frame)
                    while frame for count below 32 do
                      (push (object "index" index "frame"
                                    (bounded-name (sb-di:debug-fun-name (sb-di:frame-debug-fun frame)))) frames)
                      (incf index))
              (loop for restart in (compute-restarts condition) for count below 32 do
                (let ((name (restart-name restart)))
                  (push (object "name" (and name (bounded-name name))
                                "description" "Active restart; project report omitted") restarts)))
              (setf answer
                    (json-text
                     (object "condition" (object "type" (bounded-name (type-of condition))
                                                 "text" "Trusted condition identity; project report omitted"
                                                 "fallback" :true)
                             "backtrace" (coerce (nreverse frames) 'vector)
                             "restarts" (coerce (nreverse restarts) 'vector)
                             "truncated" :true "capture_failed" :false)
                     remaining))))
        (error () nil)))
    ;; One ASCII byte is always reserved, even when project output used the
    ;; rest of B. No callback or introspection is attempted on this path.
    (or answer "0")))

(defvar *generation*)
(defvar *directory*)
(defvar *worker* nil)
(defvar *request* nil)
(defvar *outcome* nil)
(defvar *cancel-tag* nil)
(defvar *output* *standard-output*)
(defvar *operation-id* nil)
(defvar *operation-generation* nil)
(defvar *operation-lease* nil)

(defun evaluate-source (source kind)
  (cond ((string= kind "compile_source")
         (let* ((base (merge-pathnames (concatenate 'string (getf *request* :operation-id) ".source.lisp") *directory*))
                (output (make-pathname :type "fasl" :defaults base)))
           (unwind-protect
                (progn
                  (with-open-file (stream base :direction :output :if-exists :error
                                              :external-format :utf-8)
                    (write-string source stream))
                  (multiple-value-bind (path warnings failure) (compile-file base :output-file output)
                    (declare (ignore warnings))
                    (when failure (error "Source compilation failed"))
                    (namestring path)))
             (when (probe-file base) (delete-file base))
             (when (probe-file output) (delete-file output)))))
        (t
         ;; Read/evaluate incrementally: a later reader or execution failure
         ;; preserves earlier effects and cannot claim rollback.
         (with-input-from-string (stream source)
           (loop with result = nil for form = (read stream nil stream)
                 until (eq form stream) do (setf result (eval form))
                 finally (return result))))))

(defun run-operation (request tag)
  (let* ((*package* (or (and (getf (getf request :context) :namespace)
                            (find-package (getf (getf request :context) :namespace)))
                       (find-package :cl-user)))
         (*readtable* (copy-readtable nil)) (*read-eval* t)
         (*print-level* 6) (*print-length* 32) (*print-circle* t)
         (*print-pretty* nil) (*print-readably* nil)
         (*operation-id* (getf request :operation-id))
         (*operation-generation* *generation*)
         (*operation-lease* (getf request :expected-lease-epoch))
         (*default-pathname-defaults*
           (if (getf (getf request :context) :working-dir)
               (pathname (getf (getf request :context) :working-dir)) *default-pathname-defaults*))
         (limits (getf request :limits))
         (budget (min 16384 (or (getf limits :output-bytes) 16384)))
         (seconds (min .25 (or (getf limits :timeout-seconds) .25)))
         (stream (make-instance 'bounded-stream :limit (max 0 (1- budget))))
         (*standard-output* stream) (*error-output* stream) (*trace-output* stream)
         (*debug-io* (make-two-way-stream (make-string-input-stream "") stream))
         (*query-io* *debug-io*) (*terminal-io* *debug-io*)
         (diagnostic nil) (status "cancelled") (result nil) (consistent nil))
    (catch tag
      (block execution
        (handler-bind
            ((error (lambda (condition)
                      ;; Prevent recursive capture on trusted metadata failures.
                      (let ((raw (handler-case
                                     (capture-condition condition seconds (- budget (byte-count stream)))
                                   (error () "0"))))
                        (setf diagnostic raw status "condition_signalled")
                        (return-from execution nil)))))
          (setf result (evaluate-source (getf (getf request :payload) :expression) (getf request :kind)))
          ;; Rendering uses the same finite timer and remaining byte budget.
          ;; Unsupported/oversized values signal within the original context.
          (if (<= seconds 0)
              (error "Result rendering deadline exhausted")
              (sb-ext:with-timeout seconds (json-text result (- budget (byte-count stream)))))
          (when (truncated-p stream) (error "Project output truncated"))
          (setf status "completed" consistent t))))
    ;; Reaching here means every project UNWIND-PROTECT has completed. The main
    ;; control thread waits for actual worker death before emitting this value.
    (list :status status :result (if (string= status "completed") result nil)
          :diagnostic diagnostic :consistent consistent
          :output (copy-seq (buffer stream)))))

(defun publish-completion ()
  (when (and *worker* (not (sb-thread:thread-alive-p *worker*)))
    (sb-thread:join-thread *worker*)
    (let ((request *request*) (outcome *outcome*))
      ;; Project output has already been bounded in the worker. Emit before
      ;; protocol completion so the supervisor can drain it before publication.
      (write-string (getf outcome :output) *output*) (finish-output *output*)
      (send-frame
       (object "type" "result" "session_id" (getf request :session-id)
               "operation_id" (getf request :operation-id) "generation" (generation-json *generation*)
               "lease_epoch" (getf request :expected-lease-epoch)
               "status" (getf outcome :status) "result" (getf outcome :result)
               "image_consistent" (truth (getf outcome :consistent))
               "cancellation_confirmed" (truth (string= (getf outcome :status) "cancelled"))
               "diagnostic" (getf outcome :diagnostic)))
      (setf *worker* nil *outcome* nil *cancel-tag* nil))))

(defun main ()
  (let ((init (receive-frame)))
    (unless (string= (getf init :type) "init") (error "Expected init"))
    (setf *generation* (getf init :generation) *directory* (pathname (getf init :directory)))
    (send-frame (object "type" "ready" "generation" (generation-json *generation*))))
  (loop
    (publish-completion)
    (when (listen *standard-input*)
      (let ((frame (receive-frame)))
        (unless (equal (getf frame :generation) *generation*) (error "Wrong generation"))
        (cond
          ((string= (getf frame :type) "execute")
           (when *worker* (error "Worker busy"))
           (let ((request (getf frame :request)) (tag (gensym "CANCEL")))
             (setf *request* request *cancel-tag* tag)
             (setf *worker*
                   (sb-thread:make-thread
                    (lambda () (setf *outcome* (run-operation request tag)))
                    :name "nizam-operation"))))
          ((string= (getf frame :type) "cancel")
           (when (and *worker* (sb-thread:thread-alive-p *worker*)
                      (equal (getf frame :session-id) (getf *request* :session-id))
                      (equal (getf frame :operation-id) (getf *request* :operation-id))
                      (eql (getf frame :lease-epoch) (getf *request* :expected-lease-epoch)))
             (let ((tag *cancel-tag*))
               (sb-thread:interrupt-thread *worker* (lambda () (throw tag nil))))))
          (t (error "Invalid private frame")))))
    (sleep .005)))
(main)
