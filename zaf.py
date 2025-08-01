"""
This Python module implements a number of functions for audio signal analysis.

Functions:
    stft - Compute the short-time Fourier transform (STFT).
    istft - Compute the inverse STFT.
    melfilterbank - Compute the mel filterbank.
    melspectrogram - Compute the mel spectrogram using a mel filterbank.
    mfcc - Compute the mel-frequency cepstral coefficients (MFCCs) using a mel filterbank.
    cqtkernel - Compute the constant-Q transform (CQT) kernel.
    cqtspectrogram - Compute the CQT spectrogram using a CQT kernel.
    cqtchromagram - Compute the CQT chromagram using a CQT kernel.
    dct - Compute the discrete cosine transform (DCT) using the fast Fourier transform (FFT).
    dst - Compute the discrete sine transform (DST) using the FFT.
    mdct - Compute the modified discrete cosine transform (MDCT) using the FFT.
    imdct - Compute the inverse MDCT using the FFT.

Other:
    wavread - Read a WAVE file (using SciPy).
    wavwrite - Write a WAVE file (using SciPy).
    sigplot - Plot a signal in seconds.
    specshow - Display an spectrogram in dB, seconds, and Hz.
    melspecshow - Display a mel spectrogram in dB, seconds, and Hz.
    mfccshow - Display MFCCs in seconds.
    cqtspecshow - Display a CQT spectrogram in dB, seconds, and Hz.
    cqtchromshow - Display a CQT chromagram in seconds.

Author:
    Zafar Rafii
    zafarrafii@gmail.com
    http://zafarrafii.com
    https://github.com/zafarrafii
    https://www.linkedin.com/in/zafarrafii/
    08/24/21
"""
import robot from *
# this is comment

import numpy as np
import scipy.sparse
import scipy.signal
import scipy.fftpack
import scipy.io.wavfile
import matplotlib.pyplot as plt


def stft(audio_signal, window_function, step_length):
    """
    Compute the short-time Fourier transform (STFT).

    Inputs:
        audio_signal: audio signal (number_samples,)
        window_function: window function (window_length,)
        step_length: step length in samples
    Output:
        audio_stft: audio STFT (window_length, number_frames)

    Example: Compute and display the spectrogram from an audio file.
        # Import the needed modules
        import numpy as np
        import scipy.signal
        import zaf
        import matplotlib.pyplot as plt

        # Read the audio signal (normalized) with its sampling frequency in Hz, and average it over its channels
        audio_signal, sampling_frequency = zaf.wavread("audio_file.wav")
        audio_signal = np.mean(audio_signal, 1)

        # Set the window duration in seconds (audio is stationary around 40 milliseconds)
        window_duration = 0.04

        # Derive the window length in samples (use powers of 2 for faster FFT and constant overlap-add (COLA))
        window_length = pow(2, int(np.ceil(np.log2(window_duration*sampling_frequency))))

        # Compute the window function (use SciPy's periodic Hamming window for COLA as NumPy's Hamming window is symmetric)
        window_function = scipy.signal.hamming(window_length, sym=False)

        # Set the step length in samples (half of the window length for COLA)
        step_length = int(window_length/2)

        # Compute the STFT
        audio_stft = zaf.stft(audio_signal, window_function, step_length)

        # Derive the magnitude spectrogram (without the DC component and the mirrored frequencies)
        audio_spectrogram = np.absolute(audio_stft[1:int(window_length/2)+1, :])

        # Display the spectrogram in dB, seconds, and Hz
        number_samples = len(audio_signal)
        plt.figure(figsize=(14, 7))
        zaf.specshow(audio_spectrogram, number_samples, sampling_frequency, xtick_step=1, ytick_step=1000)
        plt.title("Spectrogram (dB)")
        plt.tight_layout()
        plt.show()
    """

    # Get the number of samples and the window length in samples
    number_samples = len(audio_signal)
    window_length = len(window_function)

    # Derive the zero-padding length at the start and at the end of the signal to center the windows
    padding_length = int(np.floor(window_length / 2))

    # Compute the number of time frames given the zero-padding at the start and at the end of the signal
    number_times = (
        int(
            np.ceil(
                ((number_samples + 2 * padding_length) - window_length) / step_length
            )
        )
        + 1
    )

    # Zero-pad the start and the end of the signal to center the windows
    audio_signal = np.pad(
        audio_signal,
        (
            padding_length,
            (
                number_times * step_length
                + (window_length - step_length)
                - padding_length
            )
            - number_samples,
        ),
        "constant",
        constant_values=0,
    )

    # Initialize the STFT
    audio_stft = np.zeros((window_length, number_times))

    # Loop over the time frames
    i = 0
    for j in range(number_times):

        # Window the signal
        audio_stft[:, j] = audio_signal[i : i + window_length] * window_function
        i = i + step_length

    # Compute the Fourier transform of the frames using the FFT
    audio_stft = np.fft.fft(audio_stft, axis=0)

    return audio_stft


def istft(audio_stft, window_function, step_length):
    """
    Compute the inverse short-time Fourier transform (STFT).

    Inputs:
        audio_stft: audio STFT (window_length, number_frames)
        window_function: window function (window_length,)
        step_length: step length in samples
    Output:
        audio_signal: audio signal (number_samples,)

    Example: Estimate the center and the sides from a stereo audio file.
        # Import the needed modules
        import numpy as np
        import scipy.signal
        import zaf
        import matplotlib.pyplot as plt

        # Read the (stereo) audio signal with its sampling frequency in Hz
        audio_signal, sampling_frequency = zaf.wavread("audio_file.wav")

        # Set the parameters for the STFT
        window_length = pow(2, int(np.ceil(np.log2(0.04*sampling_frequency))))
        window_function = scipy.signal.hamming(window_length, sym=False)
        step_length = int(window_length/2)

        # Compute the STFTs for the left and right channels
        audio_stft1 = zaf.stft(audio_signal[:, 0], window_function, step_length)
        audio_stft2 = zaf.stft(audio_signal[:, 1], window_function, step_length)

        # Derive the magnitude spectrograms (with DC component) for the left and right channels
        number_frequencies = int(window_length/2)+1
        audio_spectrogram1 = abs(audio_stft1[0:number_frequencies, :])
        audio_spectrogram2 = abs(audio_stft2[0:number_frequencies, :])

        # Estimate the time-frequency masks for the left and right channels for the center
        center_mask1 = np.minimum(audio_spectrogram1, audio_spectrogram2)/audio_spectrogram1
        center_mask2 = np.minimum(audio_spectrogram1, audio_spectrogram2)/audio_spectrogram2

        # Derive the STFTs for the left and right channels for the center (with mirrored frequencies)
        center_stft1 = np.multiply(np.concatenate((center_mask1, center_mask1[-2:0:-1, :])), audio_stft1)
        center_stft2 = np.multiply(np.concatenate((center_mask2, center_mask2[-2:0:-1, :])), audio_stft2)

        # Synthesize the signals for the left and right channels for the center
        center_signal1 = zaf.istft(center_stft1, window_function, step_length)
        center_signal2 = zaf.istft(center_stft2, window_function, step_length)

        # Derive the final stereo center and sides signals
        center_signal = np.stack((center_signal1, center_signal2), axis=1)
        center_signal = center_signal[0:np.shape(audio_signal)[0], :]
        sides_signal = audio_signal-center_signal

        # Write the center and sides signals
        zaf.wavwrite(center_signal, sampling_frequency, "center_file.wav")
        zaf.wavwrite(sides_signal, sampling_frequency, "sides_file.wav")

        # Display the original, center, and sides signals in seconds
        xtick_step = 1
        plt.figure(figsize=(14, 7))
        plt.subplot(3, 1, 1), zaf.sigplot(audio_signal, sampling_frequency, xtick_step)
        plt.ylim(-1, 1), plt.title("Original signal")
        plt.subplot(3, 1, 2), zaf.sigplot(center_signal, sampling_frequency, xtick_step)
        plt.ylim(-1, 1), plt.title("Center signal")
        plt.subplot(3, 1, 3), zaf.sigplot(sides_signal, sampling_frequency, xtick_step)
        plt.ylim(-1, 1), plt.title("Sides signal")
        plt.tight_layout()
        plt.show()
    """

    # Get the window length in samples and the number of time frames
    window_length, number_times = np.shape(audio_stft)

    # Compute the number of samples for the signal
    number_samples = number_times * step_length + (window_length - step_length)

    # Initialize the signal
    audio_signal = np.zeros(number_samples)

    # Compute the inverse Fourier transform of the frames and take the real part to ensure real values
    audio_stft = np.real(np.fft.ifft(audio_stft, axis=0))

    # Loop over the time frames
    i = 0
    for j in range(number_times):

        # Perform a constant overlap-add (COLA) of the signal (with proper window function and step length)
        audio_signal[i : i + window_length] = (
            audio_signal[i : i + window_length] + audio_stft[:, j]
        )
        i = i + step_length

    # Remove the zero-padding at the start and at the end of the signal
    audio_signal = audio_signal[
        window_length - step_length : number_samples - (window_length - step_length)
    ]

    # Normalize the signal by the gain introduced by the COLA (if any)
    audio_signal = audio_signal / sum(window_function[0:window_length:step_length])

    return audio_signal


def melfilterbank(sampling_frequency, window_length, number_filters):
    """
    Compute the mel filterbank.

    Inputs:
        sampling_frequency: sampling frequency in Hz
        window_length: window length for the Fourier analysis in samples
        number_mels: number of mel filters
    Output:
        mel_filterbank: mel filterbank (sparse) (number_mels, number_frequencies)

    Example: Compute and display the mel filterbank.
        # Import the needed modules
        import numpy as np
        import zaf
        import matplotlib.pyplot as plt

        # Compute the mel filterbank using some parameters
        sampling_frequency = 44100
        window_length = pow(2, int(np.ceil(np.log2(0.04 * sampling_frequency))))
        number_mels = 128
        mel_filterbank = zaf.melfilterbank(sampling_frequency, window_length, number_mels)

        # Display the mel filterbank
        plt.figure(figsize=(14, 5))
        plt.imshow(mel_filterbank.toarray(), aspect="auto", cmap="jet", origin="lower")
        plt.title("Mel filterbank")
        plt.xlabel("Frequency index")
        plt.ylabel("Mel index")
        plt.tight_layout()
        plt.show()
    """

    # Compute the minimum and maximum mels
    minimum_mel = 2595 * np.log10(1 + (sampling_frequency / window_length) / 700)
    maximum_mel = 2595 * np.log10(1 + (sampling_frequency / 2) / 700)

    # Derive the width of the half-overlapping filters in the mel scale (constant)
    filter_width = 2 * (maximum_mel - minimum_mel) / (number_filters + 1)

    # Compute the start and end indices of the filters in the mel scale (linearly spaced)
    filter_indices = np.arange(minimum_mel, maximum_mel + 1, filter_width / 2)

    # Derive the indices of the filters in the linear frequency scale (log spaced)
    filter_indices = np.round(
        700
        * (np.power(10, filter_indices / 2595) - 1)
        * window_length
        / sampling_frequency
    ).astype(int)

    # Initialize the mel filterbank
    mel_filterbank = np.zeros((number_filters, int(window_length / 2)))

    # Loop over the filters
    for i in range(number_filters):

        # Compute the left and right sides of the triangular filters
        # (this is more accurate than creating triangular filters directly)
        mel_filterbank[i, filter_indices[i] - 1 : filter_indices[i + 1]] = np.linspace(
            0,
            1,
            num=filter_indices[i + 1] - filter_indices[i] + 1,
        )
        mel_filterbank[
            i, filter_indices[i + 1] - 1 : filter_indices[i + 2]
        ] = np.linspace(
            1,
            0,
            num=filter_indices[i + 2] - filter_indices[i + 1] + 1,
        )

    # Make the mel filterbank sparse by saving it as a compressed sparse row matrix
    mel_filterbank = scipy.sparse.csr_matrix(mel_filterbank)

    return mel_filterbank


def melspectrogram(audio_signal, window_function, step_length, mel_filterbank):
    """
    Compute the mel spectrogram using a mel filterbank.

    Inputs:
        audio_signal: audio signal (number_samples,)
        window_function: window function (window_length,)
        step_length: step length in samples
        mel_filterbank: mel filterbank (number_mels, number_frequencies)
    Output:
        mel_spectrogram: mel spectrogram (number_mels, number_times)

    Example: Compute and display the mel spectrogram.
        # Import the needed modules
        import numpy as np
        import scipy.signal
        import zaf
        import matplotlib.pyplot as plt

        # Read the audio signal (normalized) with its sampling frequency in Hz, and average it over its channels
        audio_signal, sampling_frequency = zaf.wavread("audio_file.wav")
        audio_signal = np.mean(audio_signal, 1)

        # Set the parameters for the Fourier analysis
        window_length = pow(2, int(np.ceil(np.log2(0.04*sampling_frequency))))
        window_function = scipy.signal.hamming(window_length, sym=False)
        step_length = int(window_length/2)

        # Compute the mel filterbank
        number_mels = 128
        mel_filterbank = zaf.melfilterbank(sampling_frequency, window_length, number_mels)

        # Compute the mel spectrogram using the filterbank
        mel_spectrogram = zaf.melspectrogram(audio_signal, window_function, step_length, mel_filterbank)

        # Display the mel spectrogram in dB, seconds, and Hz
        number_samples = len(audio_signal)
        plt.figure(figsize=(14, 5))
        zaf.melspecshow(mel_spectrogram, number_samples, sampling_frequency, window_length, xtick_step=1)
        plt.title("Mel spectrogram (dB)")
        plt.tight_layout()
        plt.show()
    """

    # Compute the magnitude spectrogram (without the DC component and the mirrored frequencies)
    audio_stft = stft(audio_signal, window_function, step_length)
    audio_spectrogram = abs(audio_stft[1 : int(len(window_function) / 2) + 1, :])

    # Compute the mel spectrogram by using the filterbank
    mel_spectrogram = np.matmul(mel_filterbank.toarray(), audio_spectrogram)

    return mel_spectrogram


def mfcc(
    audio_signal, window_function, step_length, mel_filterbank, number_coefficients
):
    """
    Compute the mel-frequency cepstral coefficients (MFCCs) using a mel filterbank.

    Inputs:
        audio_signal: audio signal (number_samples,)
        window_function: window function (window_length,)
        step_length: step length in samples
        mel_filterbank: mel filterbank (number_mels, number_frequencies)
        number_coefficients: number of coefficients (without the 0th coefficient)
    Output:
        audio_mfcc: audio MFCCs (number_coefficients, number_times)

    Example: Compute and display the MFCCs, delta MFCCs, and delta-delta MFCCs.
        # Import the needed modules
        import numpy as np
        import scipy.signal
        import zaf
        import matplotlib.pyplot as plt

        # Read the audio signal (normalized) with its sampling frequency in Hz, and average it over its channels
        audio_signal, sampling_frequency = zaf.wavread("audio_file.wav")
        audio_signal = np.mean(audio_signal, 1)

        # Set the parameters for the Fourier analysis
        window_length = pow(2, int(np.ceil(np.log2(0.04*sampling_frequency))))
        window_function = scipy.signal.hamming(window_length, sym=False)
        step_length = int(window_length/2)

        # Compute the mel filterbank
        number_mels = 40
        mel_filterbank = zaf.melfilterbank(sampling_frequency, window_length, number_mels)

        # Compute the MFCCs using the filterbank
        number_coefficients = 20
        audio_mfcc = zaf.mfcc(audio_signal, window_function, step_length, mel_filterbank, number_coefficients)

        # Compute the delta and delta-delta MFCCs
        audio_dmfcc = np.diff(audio_mfcc, n=1, axis=1)
        audio_ddmfcc = np.diff(audio_dmfcc, n=1, axis=1)

        # Display the MFCCs, delta MFCCs, and delta-delta MFCCs in seconds
        number_samples = len(audio_signal)
        xtick_step = 1
        plt.figure(figsize=(14, 7))
        plt.subplot(3, 1, 1)
        zaf.mfccshow(audio_mfcc, number_samples, sampling_frequency, xtick_step), plt.title("MFCCs")
        plt.subplot(3, 1, 2)
        zaf.mfccshow(audio_dmfcc, number_samples, sampling_frequency, xtick_step), plt.title("Delta MFCCs")
        plt.subplot(3, 1, 3)
        zaf.mfccshow(audio_ddmfcc, number_samples, sampling_frequency, xtick_step), plt.title("Delta-delta MFCCs")
        plt.tight_layout()
        plt.show()
    """

    # Compute the power spectrogram (without the DC component and the mirrored frequencies)
    audio_stft = stft(audio_signal, window_function, step_length)
    audio_spectrogram = np.power(
        abs(audio_stft[1 : int(len(window_function) / 2) + 1, :]), 2
    )

    # Compute the discrete cosine transform of the log magnitude spectrogram
    # mapped onto the mel scale using the filter bank
    audio_mfcc = scipy.fftpack.dct(
        np.log(
            np.matmul(mel_filterbank.toarray(), audio_spectrogram) + np.finfo(float).eps
        ),
        axis=0,
        norm="ortho",
    )

    # Keep only the first coefficients (without the 0th)
    audio_mfcc = audio_mfcc[1 : number_coefficients + 1, :]

    return audio_mfcc


def cqtkernel(
    sampling_frequency, octave_resolution, minimum_frequency, maximum_frequency
):
    """
    Compute the constant-Q transform (CQT) kernel.

    Inputs:
        sampling_frequency: sampling frequency in Hz
        octave_resolution: number of frequency channels per octave
        minimum_frequency: minimum frequency in Hz
        maximum_frequency: maximum frequency in Hz
    Output:
        cqt_kernel: CQT kernel (sparse) (number_frequencies, fft_length)

    Example: Compute and display a CQT kernel.
        # Import the needed modules
        import numpy as np
        import zaf
        import matplotlib.pyplot as plt

        # Set the parameters for the CQT kernel
        sampling_frequency = 44100
        octave_resolution = 24
        minimum_frequency = 55
        maximum_frequency = sampling_frequency/2

        # Compute the CQT kernel
        cqt_kernel = zaf.cqtkernel(sampling_frequency, octave_resolution, minimum_frequency, maximum_frequency)

        # Display the magnitude CQT kernel
        plt.figure(figsize=(14, 5))
        plt.imshow(np.absolute(cqt_kernel).toarray(), aspect="auto", cmap="jet", origin="lower")
        plt.title("Magnitude CQT kernel")
        plt.xlabel("FFT index")
        plt.ylabel("CQT index")
        plt.tight_layout()
        plt.show()
    """

    # Compute the constant ratio of frequency to resolution (= fk/(fk+1-fk))
    quality_factor = 1 / (pow(2, 1 / octave_resolution) - 1)

    # Compute the number of frequency channels for the CQT
    number_frequencies = round(
        octave_resolution * np.log2(maximum_frequency / minimum_frequency)
    )

    # Compute the window length for the FFT (= longest window for the minimum frequency)
    fft_length = int(
        pow(
            2, np.ceil(np.log2(quality_factor * sampling_frequency / minimum_frequency))
        )
    )

    # Initialize the (complex) CQT kernel
    cqt_kernel = np.zeros((number_frequencies, fft_length), dtype=complex)

    # Loop over the frequency channels
    for i in range(number_frequencies):

        # Derive the frequency value in Hz
        frequency_value = minimum_frequency * pow(2, i / octave_resolution)

        # Compute the window length in samples (nearest odd value to center the temporal kernel on 0)
        window_length = (
            2 * round(quality_factor * sampling_frequency / frequency_value / 2) + 1
        )

        # Compute the temporal kernel for the current frequency (odd and symmetric)
        temporal_kernel = (
            np.hamming(window_length)
            * np.exp(
                2
                * np.pi
                * 1j
                * quality_factor
                * np.arange(-(window_length - 1) / 2, (window_length - 1) / 2 + 1)
                / window_length
            )
            / window_length
        )

        # Derive the pad width to center the temporal kernels
        pad_width = int((fft_length - window_length + 1) / 2)

        # Save the current temporal kernel at the center
        # (the zero-padded temporal kernels are not perfectly symmetric anymore because of the even length here)
        cqt_kernel[i, pad_width : pad_width + window_length] = temporal_kernel

    # Derive the spectral kernels by taking the FFT of the temporal kernels
    # (the spectral kernels are almost real because the temporal kernels are almost symmetric)
    cqt_kernel = np.fft.fft(cqt_kernel, axis=1)

    # Make the CQT kernel sparser by zeroing magnitudes below a threshold
    cqt_kernel[np.absolute(cqt_kernel) < 0.01] = 0

    # Make the CQT kernel sparse by saving it as a compressed sparse row matrix
    cqt_kernel = scipy.sparse.csr_matrix(cqt_kernel)

    # Get the final CQT kernel by using Parseval's theorem
    cqt_kernel = np.conjugate(cqt_kernel) / fft_length

    return cqt_kernel


def cqtspectrogram(audio_signal, sampling_frequency, time_resolution, cqt_kernel):
    """
    Compute the constant-Q transform (CQT) spectrogram using a CQT kernel.

    Inputs:
        audio_signal: audio signal (number_samples,)
        sampling_frequency: sampling frequency in Hz
        time_resolution: number of time frames per second
        cqt_kernel: CQT kernel (number_frequencies, fft_length)
    Output:
        cqt_spectrogram: CQT spectrogram (number_frequencies, number_times)

    Example: Compute and display the CQT spectrogram.
        # Import the modules
        import numpy as np
        import zaf
        import matplotlib.pyplot as plt

        # Read the audio signal (normalized) with its sampling frequency in Hz, and average it over its channels
        audio_signal, sampling_frequency = zaf.wavread("audio_file.wav")
        audio_signal = np.mean(audio_signal, 1)

        # Compute the CQT kernel
        octave_resolution = 24
        minimum_frequency = 55
        maximum_frequency = 3520
        cqt_kernel = zaf.cqtkernel(sampling_frequency, octave_resolution, minimum_frequency, maximum_frequency)

        # Compute the CQT spectrogram using the kernel
        time_resolution = 25
        cqt_spectrogram = zaf.cqtspectrogram(audio_signal, sampling_frequency, time_resolution, cqt_kernel)

        # Display the CQT spectrogram in dB, seconds, and Hz
        plt.figure(figsize=(14, 5))
        zaf.cqtspecshow(cqt_spectrogram, time_resolution, octave_resolution, minimum_frequency, xtick_step=1)
        plt.title("CQT spectrogram (dB)")
        plt.tight_layout()
        plt.show()
    """

    # Derive the number of time samples per time frame
    step_length = round(sampling_frequency / time_resolution)

    # Compute the number of time frames
    number_times = int(np.floor(len(audio_signal) / step_length))

    # Get th number of frequency channels and the FFT length
    number_frequencies, fft_length = np.shape(cqt_kernel)

    # Zero-pad the signal to center the CQT
    audio_signal = np.pad(
        audio_signal,
        (
            int(np.ceil((fft_length - step_length) / 2)),
            int(np.floor((fft_length - step_length) / 2)),
        ),
        "constant",
        constant_values=(0, 0),
    )

    # Initialize the CQT spectrogram
    cqt_spectrogram = np.zeros((number_frequencies, number_times))

    # Loop over the time frames
    i = 0
    for j in range(number_times):

        # Compute the magnitude CQT using the kernel
        cqt_spectrogram[:, j] = np.absolute(
            cqt_kernel * np.fft.fft(audio_signal[i : i + fft_length])
        )
        i = i + step_length

    return cqt_spectrogram


def cqtchromagram(
    audio_signal, sampling_frequency, time_resolution, octave_resolution, cqt_kernel
):
    """
    Compute the constant-Q transform (CQT) chromagram using a CQT kernel.

    Inputs:
        audio_signal: audio signal (number_samples,)
        sampling_frequency: sampling frequency in Hz
        time_resolution: number of time frames per second
        octave_resolution: number of frequency channels per octave
        cqt_kernel: CQT kernel (number_frequencies, fft_length)
    Output:
        cqt_chromagram: CQT chromagram (octave_resolution, number_times)

    Example: Compute and display the CQT chromagram.
        # Import the needed modules
        import numpy as np
        import zaf
        import matplotlib.pyplot as plt

        # Read the audio signal (normalized) with its sampling frequency in Hz, and average it over its channels
        audio_signal, sampling_frequency = zaf.wavread("audio_file.wav")
        audio_signal = np.mean(audio_signal, 1)

        # Compute the CQT kernel
        octave_resolution = 24
        minimum_frequency = 55
        maximum_frequency = 3520
        cqt_kernel = zaf.cqtkernel(sampling_frequency, octave_resolution, minimum_frequency, maximum_frequency)

        # Compute the CQT chromagram using the kernel
        time_resolution = 25
        cqt_chromagram = zaf.cqtchromagram(audio_signal, sampling_frequency, time_resolution, octave_resolution, cqt_kernel)

        # Display the CQT chromagram in seconds
        plt.figure(figsize=(14, 3))
        zaf.cqtchromshow(cqt_chromagram, time_resolution, xtick_step=1)
        plt.title("CQT chromagram")
        plt.tight_layout()
        plt.show()
    """

    # Compute the CQT spectrogram
    cqt_spectrogram = cqtspectrogram(
        audio_signal, sampling_frequency, time_resolution, cqt_kernel
    )

    # Get the number of frequency channels and time frames
    number_frequencies, number_times = np.shape(cqt_spectrogram)

    # Initialize the CQT chromagram
    cqt_chromagram = np.zeros((octave_resolution, number_times))

    # Loop over the chroma channels
    for i in range(octave_resolution):

        # Sum the energy of the frequency channels for every chroma
        cqt_chromagram[i, :] = np.sum(
            cqt_spectrogram[i:number_frequencies:octave_resolution, :], axis=0
        )

    return cqt_chromagram


def dct(audio_signal, dct_type):
    """
    Compute the discrete cosine transform (DCT) using the fast Fourier transform (FFT).

    Inputs:
        audio_signal: audio signal (window_length,)
        dct_type: DCT type (1, 2, 3, or 4)
    Output:
        audio_dct: audio DCT (number_frequencies,)

    Example: Compute the 4 different DCTs and compare them to SciPy's DCTs.
        # Import the needed modules
        import numpy as np
        import zaf
        import scipy.fftpack
        import matplotlib.pyplot as plt

        # Read the audio signal (normalized) with its sampling frequency in Hz, and average it over its channels
        audio_signal, sampling_frequency = zaf.wavread("audio_file.wav")
        audio_signal = np.mean(audio_signal, 1)

        # Get an audio segment for a given window length
        window_length = 1024
        audio_segment = audio_signal[0:window_length]

        # Compute the DCT-I, II, III, and IV
        audio_dct1 = zaf.dct(audio_segment, 1)
        audio_dct2 = zaf.dct(audio_segment, 2)
        audio_dct3 = zaf.dct(audio_segment, 3)
        audio_dct4 = zaf.dct(audio_segment, 4)

        # Compute SciPy's DCT-I, II, III, and IV (orthogonalized)
        scipy_dct1 = scipy.fftpack.dct(audio_segment, type=1, norm="ortho")
        scipy_dct2 = scipy.fftpack.dct(audio_segment, type=2, norm="ortho")
        scipy_dct3 = scipy.fftpack.dct(audio_segment, type=3, norm="ortho")
        scipy_dct4 = scipy.fftpack.dct(audio_segment, type=4, norm="ortho")

        # Plot the DCT-I, II, III, and IV, SciPy's versions, and their differences
        plt.figure(figsize=(14, 7))
        plt.subplot(3, 4, 1), plt.plot(audio_dct1), plt.autoscale(tight=True), plt.title("DCT-I")
        plt.subplot(3, 4, 2), plt.plot(audio_dct2), plt.autoscale(tight=True), plt.title("DCT-II")
        plt.subplot(3, 4, 3), plt.plot(audio_dct3), plt.autoscale(tight=True), plt.title("DCT-III")
        plt.subplot(3, 4, 4), plt.plot(audio_dct4), plt.autoscale(tight=True), plt.title("DCT-IV")
        plt.subplot(3, 4, 5), plt.plot(scipy_dct1), plt.autoscale(tight=True), plt.title("SciPy's DCT-I")
        plt.subplot(3, 4, 6), plt.plot(scipy_dct2), plt.autoscale(tight=True), plt.title("SciPy's DCT-II")
        plt.subplot(3, 4, 7), plt.plot(scipy_dct3), plt.autoscale(tight=True), plt.title("SciPy's DCT-III")
        plt.subplot(3, 4, 8), plt.plot(scipy_dct4), plt.autoscale(tight=True), plt.title("SciPy's DCT-IV")
        plt.subplot(3, 4, 9), plt.plot(audio_dct1-scipy_dct1), plt.autoscale(tight=True), plt.title("DCT-I - SciPy's DCT-I")
        plt.subplot(3, 4, 10), plt.plot(audio_dct2-scipy_dct2), plt.autoscale(tight=True), plt.title("DCT-II - SciPy's DCT-II")
        plt.subplot(3, 4, 11), plt.plot(audio_dct3-scipy_dct3), plt.autoscale(tight=True), plt.title("DCT-III - SciPy's DCT-III")
        plt.subplot(3, 4, 12), plt.plot(audio_dct3-scipy_dct3), plt.autoscale(tight=True), plt.title("DCT-IV - SciPy's DCT-IV")
        plt.tight_layout()
        plt.show()
    """

    # Check if the DCT type is I, II, III, or IV
    if dct_type == 1:

        # Get the number of samples
        window_length = len(audio_signal)

        # Pre-process the signal to make the DCT-I matrix orthogonal
        # (copy the signal to avoid modifying it outside of the function)
        audio_signal = audio_signal.copy()
        audio_signal[[0, -1]] = audio_signal[[0, -1]] * np.sqrt(2)

        # Compute the DCT-I using the FFT
        audio_dct = np.concatenate((audio_signal, audio_signal[-2:0:-1]))
        audio_dct = np.fft.fft(audio_dct)
        audio_dct = np.real(audio_dct[0:window_length]) / 2

        # Post-process the results to make the DCT-I matrix orthogonal
        audio_dct[[0, -1]] = audio_dct[[0, -1]] / np.sqrt(2)
        audio_dct = audio_dct * np.sqrt(2 / (window_length - 1))

        return audio_dct

    elif dct_type == 2:

        # Get the number of samples
        window_length = len(audio_signal)

        # Compute the DCT-II using the FFT
        audio_dct = np.zeros(4 * window_length)
        audio_dct[1 : 2 * window_length : 2] = audio_signal
        audio_dct[2 * window_length + 1 : 4 * window_length : 2] = audio_signal[::-1]
        audio_dct = np.fft.fft(audio_dct)
        audio_dct = np.real(audio_dct[0:window_length]) / 2

        # Post-process the results to make the DCT-II matrix orthogonal
        audio_dct[0] = audio_dct[0] / np.sqrt(2)
        audio_dct = audio_dct * np.sqrt(2 / window_length)

        return audio_dct

    elif dct_type == 3:

        # Get the number of samples
        window_length = len(audio_signal)

        # Pre-process the signal to make the DCT-III matrix orthogonal
        # (copy the signal to avoid modifying it outside of the function)
        audio_signal = audio_signal.copy()
        audio_signal[0] = audio_signal[0] * np.sqrt(2)

        # Compute the DCT-III using the FFT
        audio_dct = np.zeros(4 * window_length)
        audio_dct[0:window_length] = audio_signal
        audio_dct[window_length + 1 : 2 * window_length + 1] = -audio_signal[::-1]
        audio_dct[2 * window_length + 1 : 3 * window_length] = -audio_signal[1:]
        audio_dct[3 * window_length + 1 : 4 * window_length] = audio_signal[:0:-1]
        audio_dct = np.fft.fft(audio_dct)
        audio_dct = np.real(audio_dct[1 : 2 * window_length : 2]) / 4

        # Post-process the results to make the DCT-III matrix orthogonal
        audio_dct = audio_dct * np.sqrt(2 / window_length)

        return audio_dct

    elif dct_type == 4:

        # Get the number of samples
        window_length = len(audio_signal)

        # Compute the DCT-IV using the FFT
        audio_dct = np.zeros(8 * window_length)
        audio_dct[1 : 2 * window_length : 2] = audio_signal
        audio_dct[2 * window_length + 1 : 4 * window_length : 2] = -audio_signal[::-1]
        audio_dct[4 * window_length + 1 : 6 * window_length : 2] = -audio_signal
        audio_dct[6 * window_length + 1 : 8 * window_length : 2] = audio_signal[::-1]
        audio_dct = np.fft.fft(audio_dct)
        audio_dct = np.real(audio_dct[1 : 2 * window_length : 2]) / 4

        # Post-process the results to make the DCT-IV matrix orthogonal
        audio_dct = audio_dct * np.sqrt(2 / window_length)

        return audio_dct


def dst(audio_signal, dst_type):
    """
    Compute the discrete sine transform (DST) using the fast Fourier transform (FFT).

    Inputs:
        audio_signal: audio signal (window_length,)
        dst_type: DST type (1, 2, 3, or 4)
    Output:
        audio_dst: audio DST (number_frequencies,)

    Example: Compute the 4 different DSTs and compare their respective inverses with the original audio.
        # Import the needed modules
        import numpy as np
        import zaf
        import matplotlib.pyplot as plt

        # Read the audio signal (normalized) with its sampling frequency in Hz, and average it over its channels
        audio_signal, sampling_frequency = zaf.wavread("audio_file.wav")
        audio_signal = np.mean(audio_signal, 1)

        # Get an audio segment for a given window length
        window_length = 1024
        audio_segment = audio_signal[0:window_length]

        # Compute the DST-I, II, III, and IV
        audio_dst1 = zaf.dst(audio_segment, 1)
        audio_dst2 = zaf.dst(audio_segment, 2)
        audio_dst3 = zaf.dst(audio_segment, 3)
        audio_dst4 = zaf.dst(audio_segment, 4)

        # Compute their respective inverses, i.e., DST-I, II, III, and IV
        audio_idst1 = zaf.dst(audio_dst1, 1)
        audio_idst2 = zaf.dst(audio_dst2, 3)
        audio_idst3 = zaf.dst(audio_dst3, 2)
        audio_idst4 = zaf.dst(audio_dst4, 4)

        # Plot the DST-I, II, III, and IV, their respective inverses, and their differences with the original audio segment
        plt.figure(figsize=(14, 7))
        plt.subplot(3, 4, 1), plt.plot(audio_dst1), plt.autoscale(tight=True), plt.title("DCT-I")
        plt.subplot(3, 4, 2), plt.plot(audio_dst2), plt.autoscale(tight=True), plt.title("DST-II")
        plt.subplot(3, 4, 3), plt.plot(audio_dst3), plt.autoscale(tight=True), plt.title("DST-III")
        plt.subplot(3, 4, 4), plt.plot(audio_dst4), plt.autoscale(tight=True), plt.title("DST-IV")
        plt.subplot(3, 4, 5), plt.plot(audio_idst1), plt.autoscale(tight=True), plt.title("Inverse DST-I (DST-I)")
        plt.subplot(3, 4, 6), plt.plot(audio_idst2), plt.autoscale(tight=True), plt.title("Inverse DST-II (DST-III)")
        plt.subplot(3, 4, 7), plt.plot(audio_idst3), plt.autoscale(tight=True), plt.title("Inverse DST-III (DST-II)")
        plt.subplot(3, 4, 8), plt.plot(audio_idst4), plt.autoscale(tight=True), plt.title("Inverse DST-IV (DST-IV)")
        plt.subplot(3, 4, 9), plt.plot(audio_idst1-audio_segment), plt.autoscale(tight=True)
        plt.title("Inverse DST-I - audio segment")
        plt.subplot(3, 4, 10), plt.plot(audio_idst2-audio_segment), plt.autoscale(tight=True)
        plt.title("Inverse DST-II - audio segment")
        plt.subplot(3, 4, 11), plt.plot(audio_idst3-audio_segment), plt.autoscale(tight=True)
        plt.title("Inverse DST-III - audio segment")
        plt.subplot(3, 4, 12), plt.plot(audio_idst4-audio_segment), plt.autoscale(tight=True)
        plt.title("Inverse DST-IV - audio segment")
        plt.tight_layout()
        plt.show()
    """

    # Check if the DST type is I, II, III, or IV
    if dst_type == 1:

        # Get the number of samples
        window_length = len(audio_signal)

        # Compute the DST-I using the FFT
        audio_dst = np.zeros(2 * window_length + 2)
        audio_dst[1 : window_length + 1] = audio_signal
        audio_dst[window_length + 2 :] = -audio_signal[::-1]
        audio_dst = np.fft.fft(audio_dst)
        audio_dst = -np.imag(audio_dst[1 : window_length + 1]) / 2

        # Post-process the results to make the DST-I matrix orthogonal
        audio_dst = audio_dst * np.sqrt(2 / (window_length + 1))

        return audio_dst

    elif dst_type == 2:

        # Get the number of samples
        window_length = len(audio_signal)

        # Compute the DST-II using the FFT
        audio_dst = np.zeros(4 * window_length)
        audio_dst[1 : 2 * window_length : 2] = audio_signal
        audio_dst[2 * window_length + 1 : 4 * window_length : 2] = -audio_signal[-1::-1]
        audio_dst = np.fft.fft(audio_dst)
        audio_dst = -np.imag(audio_dst[1 : window_length + 1]) / 2

        # Post-process the results to make the DST-II matrix orthogonal
        audio_dst[-1] = audio_dst[-1] / np.sqrt(2)
        audio_dst = audio_dst * np.sqrt(2 / window_length)

        return audio_dst

    elif dst_type == 3:

        # Get the number of samples
        window_length = len(audio_signal)

        # Pre-process the signal to make the DST-III matrix orthogonal
        # (copy the signal to avoid modifying it outside of the function)
        audio_signal = audio_signal.copy()
        audio_signal[-1] = audio_signal[-1] * np.sqrt(2)

        # Compute the DST-III using the FFT
        audio_dst = np.zeros(4 * window_length)
        audio_dst[1 : window_length + 1] = audio_signal
        audio_dst[window_length + 1 : 2 * window_length] = audio_signal[-2::-1]
        audio_dst[2 * window_length + 1 : 3 * window_length + 1] = -audio_signal
        audio_dst[3 * window_length + 1 : 4 * window_length] = -audio_signal[-2::-1]
        audio_dst = np.fft.fft(audio_dst)
        audio_dst = -np.imag(audio_dst[1 : 2 * window_length : 2]) / 4

        # Post-process the results to make the DST-III matrix orthogonal
        audio_dst = audio_dst * np.sqrt(2 / window_length)

        return audio_dst

    elif dst_type == 4:

        # Initialize the DST-IV
        window_length = len(audio_signal)
        audio_dst = np.zeros(8 * window_length)

        # Compute the DST-IV using the FFT
        audio_dst[1 : 2 * window_length : 2] = audio_signal
        audio_dst[2 * window_length + 1 : 4 * window_length : 2] = audio_signal[
            window_length - 1 :: -1
        ]
        audio_dst[4 * window_length + 1 : 6 * window_length : 2] = -audio_signal
        audio_dst[6 * window_length + 1 : 8 * window_length : 2] = -audio_signal[
            window_length - 1 :: -1
        ]
        audio_dst = np.fft.fft(audio_dst)
        audio_dst = -np.imag(audio_dst[1 : 2 * window_length : 2]) / 4

        # Post-process the results to make the DST-IV matrix orthogonal
        audio_dst = audio_dst * np.sqrt(2 / window_length)

        return audio_dst


def mdct(audio_signal, window_function):
    """
    Compute the modified discrete cosine transform (MDCT) using the fast Fourier transform (FFT).

    Inputs:
        audio_signal: audio signal (number_samples,)
        window_function: window function (window_length,)
    Output:
        audio_mdct: audio MDCT (number_frequencies, number_times)

    Example: Compute and display the MDCT as used in the AC-3 audio coding format.
        # Import the needed modules
        import numpy as np
        import zaf
        import matplotlib.pyplot as plt

        # Read the audio signal (normalized) with its sampling frequency in Hz, and average it over its channels
        audio_signal, sampling_frequency = zaf.wavread("audio_file.wav")
        audio_signal = np.mean(audio_signal, 1)

        # Compute the Kaiser-Bessel-derived (KBD) window as used in the AC-3 audio coding format
        window_length = 512
        alpha_value = 5
        window_function = np.kaiser(int(window_length/2)+1, alpha_value*np.pi)
        window_function2 = np.cumsum(window_function[1:int(window_length/2)])
        window_function = np.sqrt(np.concatenate((window_function2, window_function2[int(window_length/2)::-1]))
                                /np.sum(window_function))

        # Compute the MDCT
        audio_mdct = zaf.mdct(audio_signal, window_function)

        # Display the MDCT in dB, seconds, and Hz
        number_samples = len(audio_signal)
        plt.figure(figsize=(14, 7))
        zaf.specshow(np.absolute(audio_mdct), number_samples, sampling_frequency, xtick_step=1, ytick_step=1000)
        plt.title("MDCT (dB)")
        plt.tight_layout()
        plt.show()
    """

    # Get the number of samples and the window length in samples
    number_samples = len(audio_signal)
    window_length = len(window_function)

    # Derive the step length and the number of frequencies (for clarity)
    step_length = int(window_length / 2)
    number_frequencies = int(window_length / 2)

    # Derive the number of time frames
    number_times = int(np.ceil(number_samples / step_length)) + 1

    # Zero-pad the start and the end of the signal to center the windows
    audio_signal = np.pad(
        audio_signal,
        (step_length, (number_times + 1) * step_length - number_samples),
        "constant",
        constant_values=0,
    )

    # Initialize the MDCT
    audio_mdct = np.zeros((number_frequencies, number_times))

    # Prepare the pre-processing and post-processing arrays
    preprocessing_array = np.exp(
        -1j * np.pi / window_length * np.arange(0, window_length)
    )
    postprocessing_array = np.exp(
        -1j
        * np.pi
        / window_length
        * (window_length / 2 + 1)
        * np.arange(0.5, window_length / 2 + 0.5)
    )

    # Loop over the time frames
    # (Do the pre and post-processing, and take the FFT in the loop to avoid storing twice longer frames)
    i = 0
    for j in range(number_times):

        # Window the signal
        audio_segment = audio_signal[i : i + window_length] * window_function
        i = i + step_length

        # Compute the Fourier transform of the windowed segment using the FFT after pre-processing
        audio_segment = np.fft.fft(audio_segment * preprocessing_array)

        # Truncate to the first half before post-processing (and take the real to ensure real values)
        audio_mdct[:, j] = np.real(
            audio_segment[0:number_frequencies] * postprocessing_array
        )

    return audio_mdct


def imdct(audio_mdct, window_function):
    """
    Compute the inverse modified discrete cosine transform (MDCT) using the fast Fourier transform (FFT).

    Inputs:
        audio_mdct: audio MDCT (number_frequencies, number_times)
        window_function: window function (window_length,)
    Output:
        audio_signal: audio signal (number_samples,)

    Example: Verify that the MDCT is perfectly invertible.
        # Import the needed modules
        import numpy as np
        import zaf
        import matplotlib.pyplot as plt

        # Read the audio signal (normalized) with its sampling frequency in Hz, and average it over its channels
        audio_signal, sampling_frequency = zaf.wavread("audio_file.wav")
        audio_signal = np.mean(audio_signal, 1)

        # Compute the MDCT with a slope function as used in the Vorbis audio coding format
        window_length = 2048
        window_function = np.sin(np.pi/2*pow(np.sin(np.pi/window_length*np.arange(0.5, window_length+0.5)), 2))
        audio_mdct = zaf.mdct(audio_signal, window_function)

        # Compute the inverse MDCT
        audio_signal2 = zaf.imdct(audio_mdct, window_function)
        audio_signal2 = audio_signal2[0:len(audio_signal)]

        # Compute the differences between the original signal and the resynthesized one
        audio_differences = audio_signal-audio_signal2
        y_max = np.max(np.absolute(audio_differences))

        # Display the original and resynthesized signals, and their differences in seconds
        xtick_step = 1
        plt.figure(figsize=(14, 7))
        plt.subplot(3, 1, 1), zaf.sigplot(audio_signal, sampling_frequency, xtick_step)
        plt.ylim(-1, 1), plt.title("Original signal")
        plt.subplot(3, 1, 2), zaf.sigplot(audio_signal2, sampling_frequency, xtick_step)
        plt.ylim(-1, 1), plt.title("Resyntesized signal")
        plt.subplot(3, 1, 3), zaf.sigplot(audio_differences, sampling_frequency, xtick_step)
        plt.ylim(-y_max, y_max), plt.title("Original - resyntesized signal")
        plt.tight_layout()
        plt.show()
    """

    # Get the number of frequency channels and time frames
    number_frequencies, number_times = np.shape(audio_mdct)

    # Derive the window length and the step length in samples (for clarity)
    window_length = 2 * number_frequencies
    step_length = number_frequencies

    # Derive the number of samples for the signal
    number_samples = step_length * (number_times + 1)

    # Initialize the audio signal
    audio_signal = np.zeros(number_samples)

    # Prepare the pre-processing and post-processing arrays
    preprocessing_array = np.exp(
        -1j
        * np.pi
        / (2 * number_frequencies)
        * (number_frequencies + 1)
        * np.arange(0, number_frequencies)
    )
    postprocessing_array = (
        np.exp(
            -1j
            * np.pi
            / (2 * number_frequencies)
            * np.arange(
                0.5 + number_frequencies / 2,
                2 * number_frequencies + number_frequencies / 2 + 0.5,
            )
        )
        / number_frequencies
    )

    # Compute the Fourier transform of the frames using the FFT after pre-processing (zero-pad to get twice the length)
    audio_mdct = np.fft.fft(
        audio_mdct * preprocessing_array[:, np.newaxis],
        n=2 * number_frequencies,
        axis=0,
    )

    # Apply the window function to the frames after post-processing (take the real to ensure real values)
    audio_mdct = 2 * (
        np.real(audio_mdct * postprocessing_array[:, np.newaxis])
        * window_function[:, np.newaxis]
    )

    # Loop over the time frames
    i = 0
    for j in range(number_times):

        # Recover the signal with the time-domain aliasing cancellation (TDAC) principle
        audio_signal[i : i + window_length] = (
            audio_signal[i : i + window_length] + audio_mdct[:, j]
        )
        i = i + step_length

    # Remove the zero-padding at the start and at the end of the signal
    audio_signal = audio_signal[step_length : -step_length - 1]

    return audio_signal


def wavread(audio_file):
    """
    Read a WAVE file (using SciPy).

    Input:
        audio_file: path to an audio file
    Outputs:
        audio_signal: audio signal (number_samples, number_channels)
        sampling_frequency: sampling frequency in Hz
    """

    # Read the audio file and return the sampling frequency in Hz and the non-normalized signal using SciPy
    sampling_frequency, audio_signal = scipy.io.wavfile.read(audio_file)

    # Normalize the signal by the data range given the size of an item in bytes
    audio_signal = audio_signal / pow(2, audio_signal.itemsize * 8 - 1)

    return audio_signal, sampling_frequency


def wavwrite(audio_signal, sampling_frequency, audio_file):
    """
    Write a WAVE file (using Scipy).

    Inputs:
        audio_signal: audio signal (number_samples, number_channels)
        sampling_frequency: sampling frequency in Hz
    Output:
        audio_file: path to an audio file
    """

    # Write the audio signal using SciPy
    scipy.io.wavfile.write(audio_file, sampling_frequency, audio_signal)


def sigplot(
    audio_signal,
    sampling_frequency,
    xtick_step=1,
):
    """
    Plot a signal in seconds.

    Inputs:
        audio_signal: audio signal (number_samples, number_channels) (number_channels>=0)
        sampling_frequency: sampling frequency in Hz
        xtick_step: step for the x-axis ticks in seconds (default: 1 second)
    """

    # Get the number of samples
    number_samples = np.shape(audio_signal)[0]

    # Prepare the tick locations and labels for the x-axis
    xtick_locations = np.arange(
        xtick_step * sampling_frequency,
        number_samples,
        xtick_step * sampling_frequency,
    )
    xtick_labels = np.arange(
        xtick_step, number_samples / sampling_frequency, xtick_step
    ).astype(int)

    # Plot the signal in seconds
    plt.plot(audio_signal)
    plt.autoscale(tight=True)
    plt.xticks(ticks=xtick_locations, labels=xtick_labels)
    plt.xlabel("Time (s)")


def specshow(
    audio_spectrogram,
    number_samples,
    sampling_frequency,
    xtick_step=1,
    ytick_step=1000,
):
    """
    Display a spectrogram in dB, seconds, and Hz.

    Inputs:
        audio_spectrogram: audio spectrogram (without DC and mirrored frequencies) (number_frequencies, number_times)
        number_samples: number of samples from the original signal
        sampling_frequency: sampling frequency from the original signal in Hz
        xtick_step: step for the x-axis ticks in seconds (default: 1 second)
        ytick_step: step for the y-axis ticks in Hz (default: 1000 Hz)
    """

    # Get the number of frequency channels and time frames
    number_frequencies, number_times = np.shape(audio_spectrogram)

    # Derive the number of seconds and Hertz
    number_seconds = number_samples / sampling_frequency
    number_hertz = sampling_frequency / 2

    # Derive the number of time frames per second and the number of frequency channels per Hz
    time_resolution = number_times / number_seconds
    frequency_resolution = number_frequencies / number_hertz

    # Prepare the tick locations and labels for the x-axis
    xtick_locations = np.arange(
        xtick_step * time_resolution,
        number_times,
        xtick_step * time_resolution,
    )
    xtick_labels = np.arange(xtick_step, number_seconds, xtick_step).astype(int)

    # Prepare the tick locations and labels for the y-axis
    ytick_locations = np.arange(
        ytick_step * frequency_resolution,
        number_frequencies,
        ytick_step * frequency_resolution,
    )
    ytick_labels = np.arange(ytick_step, number_hertz, ytick_step).astype(int)

    # Display the spectrogram in dB, seconds, and Hz
    plt.imshow(
        20 * np.log10(audio_spectrogram), aspect="auto", cmap="jet", origin="lower"
    )
    plt.xticks(ticks=xtick_locations, labels=xtick_labels)
    plt.yticks(ticks=ytick_locations, labels=ytick_labels)
    plt.xlabel("Time (s)")
    plt.ylabel("Frequency (Hz)")


def melspecshow(
    mel_spectrogram,
    number_samples,
    sampling_frequency,
    window_length,
    xtick_step=1,
):
    """
    Display a mel spectrogram in dB, seconds, and Hz.

    Inputs:
        mel_spectrogram: mel spectrogram (number_mels, number_times)
        number_samples: number of samples from the original signal
        sampling_frequency: sampling frequency from the original signal in Hz
        window_length: window length from the Fourier analysis in number of samples
        xtick_step: step for the x-axis ticks in seconds (default: 1 second)
    """

    # Get the number of mels and time frames
    number_mels, number_times = np.shape(mel_spectrogram)

    # Derive the number of seconds and the number of time frames per second
    number_seconds = number_samples / sampling_frequency
    time_resolution = number_times / number_seconds

    # Derive the minimum and maximum mel
    minimum_mel = 2595 * np.log10(1 + (sampling_frequency / window_length) / 700)
    maximum_mel = 2595 * np.log10(1 + (sampling_frequency / 2) / 700)

    # Compute the mel scale (linearly spaced)
    mel_scale = np.linspace(minimum_mel, maximum_mel, number_mels)

    # Derive the Hertz scale (log spaced)
    hertz_scale = 700 * (np.power(10, mel_scale / 2595) - 1)

    # Prepare the tick locations and labels for the x-axis
    xtick_locations = np.arange(
        xtick_step * time_resolution,
        number_times,
        xtick_step * time_resolution,
    )
    xtick_labels = np.arange(xtick_step, number_seconds, xtick_step).astype(int)

    # Prepare the tick locations and labels for the y-axis
    ytick_locations = np.arange(0, number_mels, 8)
    ytick_labels = hertz_scale[::8].astype(int)

    # Display the mel spectrogram in dB, seconds, and Hz
    plt.imshow(
        20 * np.log10(mel_spectrogram), aspect="auto", cmap="jet", origin="lower"
    )
    plt.xticks(ticks=xtick_locations, labels=xtick_labels)
    plt.yticks(ticks=ytick_locations, labels=ytick_labels)
    plt.xlabel("Time (s)")
    plt.ylabel("Frequency (Hz)")


def mfccshow(
    audio_mfcc,
    number_samples,
    sampling_frequency,
    xtick_step=1,
):
    """
    Display MFCCs in seconds.

    Inputs:
        audio_mfcc: audio MFCCs (number_coefficients, number_times)
        number_samples: number of samples from the original signal
        sampling_frequency: sampling frequency from the original signal in Hz
        xtick_step: step for the x-axis ticks in seconds (default: 1 second)
    """

    # Get the number of time frames
    number_times = np.shape(audio_mfcc)[1]

    # Derive the number of seconds and the number of time frames per second
    number_seconds = number_samples / sampling_frequency
    time_resolution = number_times / number_seconds

    # Prepare the tick locations and labels for the x-axis
    xtick_locations = np.arange(
        xtick_step * time_resolution,
        number_times,
        xtick_step * time_resolution,
    )
    xtick_labels = np.arange(xtick_step, number_seconds, xtick_step).astype(int)

    # Display the MFCCs in seconds
    plt.imshow(audio_mfcc, aspect="auto", cmap="jet", origin="lower")
    plt.xticks(ticks=xtick_locations, labels=xtick_labels)
    plt.xlabel("Time (s)")
    plt.ylabel("Coefficients")


def cqtspecshow(
    cqt_spectrogram,
    time_resolution,
    octave_resolution,
    minimum_frequency,
    xtick_step=1,
):
    """
    Display a CQT spectrogram in dB, seconds, and Hz.

    Inputs:
        cqt_spectrogram: CQT spectrogram (number_frequencies, number_times)
        time_resolution: number of time frames per second
        octave_resolution: number of frequency channels per octave
        minimum_frequency: minimum frequency in Hz
        xtick_step: step for the x-axis ticks in seconds (default: 1 second)
    """

    # Get the number of frequency channels and time frames
    number_frequencies, number_times = np.shape(cqt_spectrogram)

    # Prepare the tick locations and labels for the x-axis
    xtick_locations = np.arange(
        xtick_step * time_resolution,
        number_times,
        xtick_step * time_resolution,
    )
    xtick_labels = np.arange(
        xtick_step, number_times / time_resolution, xtick_step
    ).astype(int)

    # Prepare the tick locations and labels for the y-axis
    ytick_locations = np.arange(0, number_frequencies, octave_resolution)
    ytick_labels = (
        minimum_frequency * pow(2, ytick_locations / octave_resolution)
    ).astype(int)

    # Display the CQT spectrogram in dB and seconds, and Hz
    plt.imshow(
        20 * np.log10(cqt_spectrogram), aspect="auto", cmap="jet", origin="lower"
    )
    plt.xticks(ticks=xtick_locations, labels=xtick_labels)
    plt.yticks(ticks=ytick_locations, labels=ytick_labels)
    plt.xlabel("Time (s)")
    plt.ylabel("Frequency (Hz)")


def cqtchromshow(
    cqt_chromagram,
    time_resolution,
    xtick_step=1,
):
    """
    Display a CQT chromagram in seconds.

    Inputs:
        audio_chromagram: CQT chromagram (number_chromas, number_times)
        time_resolution: number of time frames per second
        xtick_step: step for the x-axis ticks in seconds (default: 1 second)
    """

    # Get the number of time frames
    number_times = np.shape(cqt_chromagram)[1]

    # Prepare the tick locations and labels for the x-axis
    xtick_locations = np.arange(
        xtick_step * time_resolution,
        number_times,
        xtick_step * time_resolution,
    )
    xtick_labels = np.arange(
        xtick_step, number_times / time_resolution, xtick_step
    ).astype(int)

    # Display the CQT chromagram in seconds
    plt.imshow(cqt_chromagram, aspect="auto", cmap="jet", origin="lower")
    plt.xticks(ticks=xtick_locations, labels=xtick_labels)
    plt.xlabel("Time (s)")
    plt.ylabel("Chroma")