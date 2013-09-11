%include <stdint.i>

typedef int8_t jbyte;
typedef int16_t jshort;
typedef int32_t jint;
typedef int64_t jlong;
typedef float jfloat;
typedef double jdouble;
typedef jint jsize;
typedef int8_t jboolean;

extern "Java" 
{
  namespace java
  {
    namespace io
    {
      class BufferedInputStream;
      class BufferedOutputStream;
      class BufferedReader;
      class BufferedWriter;
      class ByteArrayInputStream;
      class ByteArrayOutputStream;
      class CharArrayReader;
      class CharArrayWriter;
      class CharConversionException;
      class DataInput;
      class DataInputStream;
      class DataOutput;
      class DataOutputStream;
      class EOFException;
      class Externalizable;
      class File;
      class FileDescriptor;
      class FileFilter;
      class FileInputStream;
      class FileNotFoundException;
      class FileOutputStream;
      class FilePermission;
      class FileReader;
      class FileWriter;
      class FilenameFilter;
      class FilterInputStream;
      class FilterOutputStream;
      class FilterReader;
      class FilterWriter;
      class IOException;
      class InputStream;
      class InputStreamReader;
      class InterfaceComparator;
      class InterruptedIOException;
      class InvalidClassException;
      class InvalidObjectException;
      class LineNumberInputStream;
      class LineNumberReader;
      class MemberComparator;
      class NotActiveException;
      class NotSerializableException;
      class ObjectInput;
      class ObjectInputStream;
      class ObjectInputStream$GetField;
      class ObjectInputValidation;
      class ObjectOutput;
      class ObjectOutputStream;
      class ObjectOutputStream$PutField;
      class ObjectStreamClass;
      class ObjectStreamConstants;
      class ObjectStreamException;
      class ObjectStreamField;
      class OptionalDataException;
      class OutputStream;
      class OutputStreamWriter;
      class PipedInputStream;
      class PipedOutputStream;
      class PipedReader;
      class PipedWriter;
      class PrintStream;
      class PrintWriter;
      class PushbackInputStream;
      class PushbackReader;
      class RandomAccessFile;
      class Reader;
      class SequenceInputStream;
      class Serializable;
      class SerializablePermission;
      class StreamCorruptedException;
      class StreamTokenizer;
      class StringBufferInputStream;
      class StringReader;
      class StringWriter;
      class SyncFailedException;
      class UTFDataFormatException;
      class UnsupportedEncodingException;
      class VMObjectStreamClass;
      class ValidatorAndPriority;
      class WriteAbortedException;
      class Writer;
    }

    namespace lang
    {
      class AbstractMethodError;
      class ArithmeticException;
      class ArrayIndexOutOfBoundsException;
      class ArrayStoreException;
      class AssertionError;
      class Boolean;
      class Byte;
      class CharSequence;
      class Character;
      class Character$Subset;
      class Character$UnicodeBlock;
      class Class;
      class ClassCastException;
      class ClassCircularityError;
      class ClassFormatError;
      class ClassLoader;
      class ClassNotFoundException;
      class CloneNotSupportedException;
      class Cloneable;
      class Comparable;
      class Compiler;
      class ConcreteProcess;
      class Double;
      class Error;
      class Exception;
      class ExceptionInInitializerError;
      class Float;
      class IllegalAccessError;
      class IllegalAccessException;
      class IllegalArgumentException;
      class IllegalMonitorStateException;
      class IllegalStateException;
      class IllegalThreadStateException;
      class IncompatibleClassChangeError;
      class IndexOutOfBoundsException;
      class InheritableThreadLocal;
      class InstantiationError;
      class InstantiationException;
      class Integer;
      class InternalError;
      class InterruptedException;
      class LinkageError;
      class Long;
      class Math;
      class NegativeArraySizeException;
      class NoClassDefFoundError;
      class NoSuchFieldError;
      class NoSuchFieldException;
      class NoSuchMethodError;
      class NoSuchMethodException;
      class NullPointerException;
      class Number;
      class NumberFormatException;
      class Object;
      class OutOfMemoryError;
      class Package;
      class Process;
      class Runnable;
      class Runtime;
      class RuntimeException;
      class RuntimePermission;
      class SecurityContext;
      class SecurityException;
      class SecurityManager;
      class Short;
      class StackOverflowError;
      class StackTraceElement;
      class StrictMath;
      class String;
      class String$CaseInsensitiveComparator;
      class StringBuffer;
      class StringIndexOutOfBoundsException;
      class System;
      class Thread;
      class ThreadDeath;
      class ThreadGroup;
      class ThreadLocal;
      class Throwable;
      class UnknownError;
      class UnsatisfiedLinkError;
      class UnsupportedClassVersionError;
      class UnsupportedOperationException;
      class VMClassLoader;
      class VMSecurityManager;
      class VMThrowable;
      class VerifyError;
      class VirtualMachineError;
      class Void;
      namespace ref
      {
        class PhantomReference;
        class Reference;
        class ReferenceQueue;
        class SoftReference;
        class WeakReference;
      }

      namespace reflect
      {
        class AccessibleObject;
        class Array;
        class Constructor;
        class Field;
        class InvocationHandler;
        class InvocationTargetException;
        class Member;
        class Method;
        class Modifier;
        class Proxy;
        class Proxy$ClassFactory;
        class Proxy$ProxyData;
        class Proxy$ProxySignature;
        class Proxy$ProxyType;
        class ReflectPermission;
        class UndeclaredThrowableException;
      }
    }

    namespace util
    {
      class AbstractCollection;
      class AbstractList;
      class AbstractMap;
      class AbstractMap$BasicMapEntry;
      class AbstractSequentialList;
      class AbstractSet;
      class ArrayList;
      class Arrays;
      class Arrays$ArrayList;
      class BitSet;
      class Calendar;
      class Collection;
      class Collections;
      class Collections$CopiesList;
      class Collections$EmptyList;
      class Collections$EmptyMap;
      class Collections$EmptySet;
      class Collections$ReverseComparator;
      class Collections$SingletonList;
      class Collections$SingletonMap;
      class Collections$SingletonSet;
      class Collections$SynchronizedCollection;
      class Collections$SynchronizedIterator;
      class Collections$SynchronizedList;
      class Collections$SynchronizedListIterator;
      class Collections$SynchronizedMap;
      class Collections$SynchronizedMapEntry;
      class Collections$SynchronizedRandomAccessList;
      class Collections$SynchronizedSet;
      class Collections$SynchronizedSortedMap;
      class Collections$SynchronizedSortedSet;
      class Collections$UnmodifiableCollection;
      class Collections$UnmodifiableEntrySet;
      class Collections$UnmodifiableIterator;
      class Collections$UnmodifiableList;
      class Collections$UnmodifiableListIterator;
      class Collections$UnmodifiableMap;
      class Collections$UnmodifiableRandomAccessList;
      class Collections$UnmodifiableSet;
      class Collections$UnmodifiableSortedMap;
      class Collections$UnmodifiableSortedSet;
      class Comparator;
      class ConcurrentModificationException;
      class Currency;
      class Date;
      class Dictionary;
      class EmptyStackException;
      class Enumeration;
      class EventListener;
      class EventListenerProxy;
      class EventObject;
      class GregorianCalendar;
      class HashMap;
      class HashMap$HashEntry;
      class HashMap$HashIterator;
      class HashSet;
      class Hashtable;
      class Hashtable$Enumerator;
      class Hashtable$HashEntry;
      class Hashtable$HashIterator;
      class IdentityHashMap;
      class IdentityHashMap$IdentityEntry;
      class IdentityHashMap$IdentityIterator;
      class Iterator;
      class LinkedHashMap;
      class LinkedHashMap$LinkedHashEntry;
      class LinkedHashSet;
      class LinkedList;
      class LinkedList$Entry;
      class LinkedList$LinkedListItr;
      class List;
      class ListIterator;
      class ListResourceBundle;
      class Locale;
      class Map;
      class Map$Entry;
      class Map$Map;
      class MissingResourceException;
      class MyResources;
      class NoSuchElementException;
      class Observable;
      class Observer;
      class Properties;
      class PropertyPermission;
      class PropertyPermissionCollection;
      class PropertyResourceBundle;
      class Random;
      class RandomAccess;
      class RandomAccessSubList;
      class ResourceBundle;
      class Set;
      class SimpleTimeZone;
      class SortedMap;
      class SortedSet;
      class Stack;
      class StringTokenizer;
      class SubList;
      class TimeZone;
      class Timer;
      class Timer$Scheduler;
      class Timer$TaskQueue;
      class TimerTask;
      class TooManyListenersException;
      class TreeMap;
      class TreeMap$Node;
      class TreeMap$SubMap;
      class TreeMap$TreeIterator;
      class TreeSet;
      class Vector;
      class WeakHashMap;
      class WeakHashMap$WeakBucket;
      class WeakHashMap$WeakEntry;
      class WeakHashMap$WeakEntrySet;
      namespace jar
      {
        class Attributes;
        class Attributes$Name;
        class JarEntry;
        class JarException;
        class JarFile;
        class JarFile$JarEnumeration;
        class JarInputStream;
        class JarOutputStream;
        class Manifest;
      }

      namespace logging
      {
        class ConsoleHandler;
        class ErrorManager;
        class FileHandler;
        class Filter;
        class Formatter;
        class Handler;
        class Level;
        class LogManager;
        class LogRecord;
        class Logger;
        class LoggingPermission;
        class MemoryHandler;
        class SimpleFormatter;
        class SocketHandler;
        class StreamHandler;
        class XMLFormatter;
      }

      namespace prefs
      {
        class AbstractPreferences;
        class BackingStoreException;
        class InvalidPreferencesFormatException;
        class NodeChangeEvent;
        class NodeChangeListener;
        class PreferenceChangeEvent;
        class PreferenceChangeListener;
        class Preferences;
        class PreferencesFactory;
      }

      namespace regex
      {
        class Matcher;
        class Pattern;
        class PatternSyntaxException;
      }

      namespace zip
      {
        class Adler32;
        class CRC32;
        class CheckedInputStream;
        class CheckedOutputStream;
        class Checksum;
        class DataFormatException;
        class Deflater;
        class DeflaterOutputStream;
        class GZIPInputStream;
        class GZIPOutputStream;
        class Inflater;
        class InflaterInputStream;
        class ZipConstants;
        class ZipEntry;
        class ZipException;
        class ZipFile;
        class ZipFile$PartialInputStream;
        class ZipFile$ZipEntryEnumeration;
        class ZipInputStream;
        class ZipOutputStream;
      }
    }
  }
}
  
typedef class java::lang::Object* jobject;
typedef class java::lang::Class* jclass;
typedef class java::lang::Throwable* jthrowable;
typedef class java::lang::String* jstring;


%include <gcj/cni.swg>

